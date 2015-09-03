"""
Created on 2 févr. 2014

@author: inso
"""

import time
import logging
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog
from PyQt5.QtCore import QModelIndex, pyqtSlot, QDateTime, QLocale, QEvent
from PyQt5.QtGui import QIcon

from ..core.net.api import bma as qtbma
from .wot_tab import WotTabWidget
from .identities_tab import IdentitiesTabWidget
from .wallets_tab import WalletsTabWidget
from .transactions_tab import TransactionsTabWidget
from .network_tab import NetworkTabWidget
from .informations_tab import InformationsTabWidget
from . import toast
import asyncio
from ..tools.exceptions import MembershipNotFoundError, NoPeerAvailable
from ..core.registry import IdentitiesRegistry
from ..gen_resources.community_view_uic import Ui_CommunityWidget


class CommunityWidget(QWidget, Ui_CommunityWidget):

    """
    classdocs
    """

    def __init__(self, app, status_label):
        """
        Constructor
        """
        super().__init__()
        self.app = app
        self.community = None
        self.password_asker = None
        self.status_label = status_label

        self.status_info = []
        self.status_infotext = {'membership_expire_soon':
                            self.tr("Warning : Your membership is expiring soon."),
                            'warning_certifications':
                            self.tr("Warning : Your could miss certifications soon.")
                            }

        super().setupUi(self)

        self.tab_wot = WotTabWidget(self.app)

        self.tab_identities = IdentitiesTabWidget(self.app)

        self.tab_wallets = WalletsTabWidget(self.app)

        self.tab_history = TransactionsTabWidget(self.app)

        self.tab_network = NetworkTabWidget(self.app)

        self.tabs.addTab(self.tab_history,
                                 QIcon(':/icons/tx_icon'),
                                self.tr("Transactions"))

        self.tabs.addTab(self.tab_identities,
                         QIcon(':/icons/wot_icon'),
                         self.tr("Web of Trust"))

        self.tabs.addTab(self.tab_wot,
                         QIcon(':/icons/members_icon'),
                         self.tr("Search Identities"))

        self.tabs.addTab(self.tab_network,
                                 QIcon(":/icons/network_icon"),
                                 self.tr("Network"))

    def change_account(self, account):
        self.account = account
        self.tab_wot.change_account(account)
        self.tab_identities.change_account(account)

    def change_community(self, community):
        self.community = community
        self.tab_network.change_community(community)
        self.tab_wot.change_community(community)
        self.tab_history.change_community(community)
        self.tab_identities.change_community(community)

        self.community.network.new_block_mined.connect(self.refresh_block)
        self.community.network.nodes_changed.connect(self.refresh_status)
        self.community.inner_data_changed.connect(self.refresh_status)

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
            person = self.app.identities_registry.find(self.app.current_account.pubkey, self.community)
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

            certifiers_of = person.unique_valid_certifiers_of(self.app.identities_registry, self.community)
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
        if self.community:
            text = self.tr(" Block {0}").format(self.community.network.latest_block_number)

            block = self.community.get_block(self.community.network.latest_block_number)
            if block != qtbma.blockchain.Block.null_value:
                text += " ( {0} )".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(block['medianTime']),
                            QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                        ))

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

            if self.app.preferences['expert_mode']:
                label_text += self.tr(" - Median fork window : {0}").format(self.community.network.fork_window(self.community.members_pubkeys()))

            self.status_label.setText(label_text)

    def showEvent(self, event):
        self.refresh_status()

    def referential_changed(self):
        if self.tab_history.table_history.model():
            self.tab_history.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])
            self.tab_history.refresh_balance()

    def send_membership_demand(self):
        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return
        asyncio.async(self.account.send_membership(password, self.community, 'IN'))

    def send_membership_leaving(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            asyncio.async(self.account.send_membership(password, self.community, 'OUT'))

    def handle_membership_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
        else:
            QMessageBox.information(self, self.tr("Membership"), self.tr("Success sending Membership demand"))

    def handle_revoke_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Revoke"), self.tr("Success sending Revoke demand"))
        else:
            QMessageBox.information(self, self.tr("Revoke"), self.tr("Success sending Revoke demand"))

    def handle_selfcert_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Self Certification"), self.tr("Success sending Self Certification document"))
        else:
            QMessageBox.information(self.tr("Self Certification"), self.tr("Success sending Self Certification document"))

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh_status()
        return super(CommunityWidget, self).changeEvent(event)
