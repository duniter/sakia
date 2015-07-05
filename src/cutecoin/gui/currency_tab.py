"""
Created on 2 févr. 2014

@author: inso
"""

import time
import logging
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QModelIndex, pyqtSlot, QDateTime
from PyQt5.QtGui import QIcon
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget

from .community_tab import CommunityTabWidget
from .wallets_tab import WalletsTabWidget
from .transactions_tab import TransactionsTabWidget
from .network_tab import NetworkTabWidget
from .informations_tab import InformationsTabWidget
from . import toast
import asyncio
from ..tools.exceptions import MembershipNotFoundError
from ..core.registry import IdentitiesRegistry


class CurrencyTabWidget(QWidget, Ui_CurrencyTabWidget):

    """
    classdocs
    """

    def __init__(self, app, community, password_asker, status_label):
        """
        Constructor
        """
        super().__init__()
        self.app = app
        self.community = community
        self.password_asker = password_asker
        self.status_label = status_label

        self.status_info = []
        self.status_infotext = {'membership_expire_soon':
                            self.tr("Warning : Your membership is expiring soon."),
                            'warning_certifications':
                            self.tr("Warning : Your could miss certifications soon.")
                            }

        super().setupUi(self)

        self.tab_community = CommunityTabWidget(self.app,
                                                self.app.current_account,
                                                    self.community,
                                                    self.password_asker,
                                                    self)

        self.tab_wallets = WalletsTabWidget(self.app,
                                            self.app.current_account,
                                            self.community,
                                            self.password_asker)

        self.tab_history = TransactionsTabWidget(self.app,
                                                 self.community,
                                                 self.password_asker,
                                                 self)

        self.tab_informations = InformationsTabWidget(self.app,
                                                self.community)

        self.tab_network = NetworkTabWidget(self.app,
                                            self.community)

        self.tabs_account.addTab(self.tab_wallets,
                                 QIcon(':/icons/wallet_icon'),
                                self.tr("Wallets"))

        self.tabs_account.addTab(self.tab_history,
                                 QIcon(':/icons/tx_icon'),
                                self.tr("Transactions"))

        self.tabs_account.addTab(self.tab_informations,
                                 QIcon(':/icons/informations_icon'),
                                self.tr("Informations"))

        self.tabs_account.addTab(self.tab_community,
                                 QIcon(':/icons/community_icon'),
                                self.tr("Community"))

        self.tabs_account.addTab(self.tab_network,
                                 QIcon(":/icons/network_icon"),
                                 self.tr("Network"))

        self.community.network.new_block_mined.connect(self.refresh_block)
        self.community.network.nodes_changed.connect(self.refresh_status)

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    @pyqtSlot(int)
    def refresh_block(self, block_number):
        """
        When a new block is found, start handling data.
        @param: block_number: The number of the block mined
        """
        logging.debug("Refresh block")
        self.status_info.clear()
        try:
            person = self.app.identities_registry.lookup(self.app.current_account.pubkey, self.community)
            expiration_time = person.membership_expiration_time(self.community)
            sig_validity = self.community.parameters['sigValidity']
            warning_expiration_time = int(sig_validity / 3)
            will_expire_soon = (expiration_time < warning_expiration_time)

            logging.debug("Try")
            if will_expire_soon:
                days = int(expiration_time / 3600 / 24)
                if days > 0:
                    self.status_info.append('membership_expire_soon')

                    if self.app.preferences['notifications']:
                        toast.display(self.tr("Membership expiration"),
                                  self.tr("<b>Warning : Membership expiration in {0} days</b>").format(days))

            certifiers_of = person.unique_valid_certifiers_of(self.community)
            if len(certifiers_of) < self.community.parameters['sigQty']:
                self.status_info.append('warning_certifications')
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Certifications number"),
                              self.tr("<b>Warning : You are certified by only {0} persons, need {1}</b>")
                              .format(len(certifiers_of),
                                     self.community.parameters['sigQty']))

        except MembershipNotFoundError as e:
            pass

        self.tab_history.start_progress()
        self.refresh_data()

    def refresh_wallets(self):
        if self.tab_wallets:
            self.tab_wallets.refresh()

    def refresh_data(self):
        """
        Refresh data when the blockchain watcher finished handling datas
        """
        if self.tab_wallets:
            self.tab_wallets.refresh()

        self.tab_history.refresh_balance()
        self.refresh_status()

    @pyqtSlot()
    def refresh_status(self):
        """
        Refresh status bar
        """
        logging.debug("Refresh status")
        text = self.tr(" Block {0}").format(self.community.network.latest_block)
        if self.community.network.quality > 0.66:
            icon = '<img src=":/icons/connected" width="12" height="12"/>'
        elif self.community.network.quality > 0.33:
            icon = '<img src=":/icons/weak_connect" width="12" height="12"/>'
        else:
            icon = '<img src=":/icons/disconnected" width="12" height="12"/>'
        status_infotext = " - ".join([self.status_infotext[info] for info in self.status_info])
        label_text = "{0}{1}".format(icon, text)
        if status_infotext != "":
            label_text += " - {0}".format(status_infotext)
        self.status_label.setText(label_text)

    def showEvent(self, event):
        asyncio.async(self.community.network.discover_network())
        self.refresh_status()

    def referential_changed(self):
        if self.tab_history.table_history.model():
            self.tab_history.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])
            self.tab_history.refresh_balance()

        if self.tab_wallets:
            self.tab_wallets.refresh()

        if self.tab_informations:
            self.tab_informations.refresh()
