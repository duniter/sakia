"""
Created on 2 févr. 2014

@author: inso
"""

import logging
import time
from duniterpy.api import errors
from PyQt5.QtCore import pyqtSlot, QDateTime, QLocale, QEvent, QT_TRANSLATE_NOOP, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QPushButton, QTabBar, QAction, QMenu, QFileDialog

from .graphs.wot_tab import WotTabWidget
from .widgets import toast
from .identities_tab import IdentitiesTabWidget
from .informations_tab import InformationsTabWidget
from .network_tab import NetworkTabWidget
from .transactions_tab import TransactionsTabWidget
from .graphs.explorer_tab import ExplorerTabWidget
from ..presentation.community_view_uic import Ui_CommunityWidget
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..tools.exceptions import MembershipNotFoundError, LookupFailureError, NoPeerAvailable


class CommunityWidget(QWidget, Ui_CommunityWidget):

    """
    classdocs
    """

    _tab_history_label = QT_TRANSLATE_NOOP("CommunityWidget", "Transactions")
    _tab_wot_label = QT_TRANSLATE_NOOP("CommunityWidget", "Web of Trust")
    _tab_identities_label = QT_TRANSLATE_NOOP("CommunityWidget", "Search Identities")
    _tab_network_label = QT_TRANSLATE_NOOP("CommunityWidget", "Network")
    _tab_informations_label = QT_TRANSLATE_NOOP("CommunityWidget", "Informations")

    def __init__(self, app, status_label, label_icon):
        """
        Constructor
        """
        super().__init__()
        self.app = app
        self.account = None
        self.community = None
        self.password_asker = None
        self.status_label = status_label
        self.label_icon = label_icon

        self.status_info = []

        self.tab_wot = WotTabWidget(self.app)
        self.tab_identities = IdentitiesTabWidget(self.app)
        self.tab_history = TransactionsTabWidget(self.app)
        self.tab_informations = InformationsTabWidget(self.app)
        self.tab_network = NetworkTabWidget(self.app)
        self.tab_explorer = ExplorerTabWidget(self.app)

        super().setupUi(self)

        self.tab_identities.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_identities.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot.widget))
        self.tab_history.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_history.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot.widget))
        self.tab_identities.money_sent.connect(lambda: self.tab_history.ui.table_history.model().sourceModel().refresh_transfers())
        self.tab_wot.money_sent.connect(lambda: self.tab_history.ui.table_history.model().sourceModel().refresh_transfers())

        self.tabs.addTab(self.tab_history.widget,
                                 QIcon(':/icons/tx_icon'),
                                self.tr(CommunityWidget._tab_history_label))

        self.tabs.addTab(self.tab_wot.widget,
                         QIcon(':/icons/wot_icon'),
                         self.tr(CommunityWidget._tab_wot_label))

        self.tabs.addTab(self.tab_identities.widget,
                         QIcon(':/icons/members_icon'),
                         self.tr(CommunityWidget._tab_identities_label))

        self.tabs.addTab(self.tab_network,
                                 QIcon(":/icons/network_icon"),
                                 self.tr("Network"))

    def show_closable_tab(self, tab, icon, title):
        if self.tabs.indexOf(tab) == -1:
            self.tabs.addTab(tab, icon, title)
            style = self.app.qapp.style()
            icon = style.standardIcon(style.SP_DockWidgetCloseButton)
            close_button = QPushButton(icon, '')
            close_button.clicked.connect(lambda: self.tabs.removeTab(self.tabs.indexOf(tab)))
            close_button.setStyleSheet('border-style: inset;')
            self.tabs.tabBar().setTabButton(self.tabs.indexOf(tab), QTabBar.RightSide, close_button)

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_block)
        cancel_once_task(self, self.refresh_status)
        logging.debug("Cancelled status")
        cancel_once_task(self, self.refresh_quality_buttons)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()

        self.account = account

        self.password_asker = password_asker
        self.tab_wot.change_account(account, self.password_asker)
        self.tab_identities.change_account(account, self.password_asker)
        self.tab_history.change_account(account, self.password_asker)
        self.tab_informations.change_account(account)
        self.tab_explorer.change_account(account, self.password_asker)

    def change_community(self, community):
        self.cancel_once_tasks()

        self.tab_network.change_community(community)
        self.tab_wot.change_community(community)
        self.tab_history.change_community(community)
        self.tab_identities.change_community(community)
        self.tab_informations.change_community(community)
        self.tab_explorer.change_community(community)

        if self.community:
            self.community.network.new_block_mined.disconnect(self.refresh_block)
            self.community.network.nodes_changed.disconnect(self.refresh_status)
        if community:
            community.network.new_block_mined.connect(self.refresh_block)
            community.network.nodes_changed.connect(self.refresh_status)
            self.label_currency.setText(community.currency)
        logging.debug("Changed community to {0}".format(community))
        self.button_membership.setText(self.tr("Membership"))
        self.button_membership.setEnabled(False)
        self.button_certification.setEnabled(False)
        self.action_publish_uid.setEnabled(False)
        self.community = community
        self.refresh_status()
        self.refresh_quality_buttons()

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    @once_at_a_time
    @asyncify
    async def refresh_block(self, block_number):
        """
        When a new block is found, start handling data.
        @param: block_number: The number of the block mined
        """
        logging.debug("Refresh block")
        self.status_info.clear()
        try:
            person = await self.app.identities_registry.future_find(self.app.current_account.pubkey, self.community)
            expiration_time = await person.membership_expiration_time(self.community)
            revokation_time = await person.identity_revocation_time(self.community)
            parameters = await self.community.parameters()
            sig_validity = parameters['sigValidity']
            warning_expiration_time = int(sig_validity / 3)
            will_expire_soon = (expiration_time < warning_expiration_time)
            revokation_soon = (revokation_time < 2*warning_expiration_time)
            if revokation_soon:
                days = int(revokation_time / 3600 / 24)
                if 'warning_revokation' not in self.status_info:
                    self.status_info.append('warning_revokation')

                if self.app.preferences['notifications'] and \
                        self.account.notifications['warning_revokation'][1]+24*3600 < time.time():
                    toast.display(self.tr("Identity revokation"),
                              self.tr("<b>Warning : Your identity will be implicitely revoked\
                               if you dont renew before {0} days</b>").format(days))
                    self.account.notifications['warning_revokation'][1] = time.time()
            elif will_expire_soon:
                days = int(expiration_time / 3600 / 24)
                if days > 0:
                    if 'membership_expire_soon' not in self.status_info:
                        self.status_info.append('membership_expire_soon')

                    if self.app.preferences['notifications'] and\
                            self.account.notifications['membership_expire_soon'][1]+24*3600 < time.time():
                        toast.display(self.tr("Membership expiration"),
                                  self.tr("<b>Warning : Membership expiration in {0} days</b>").format(days))
                        self.account.notifications['membership_expire_soon'][1] = time.time()

            certifiers_of = await person.unique_valid_certifiers_of(self.app.identities_registry,
                                                                         self.community)
            if len(certifiers_of) < parameters['sigQty']:
                if 'warning_certifications' not in self.status_info:
                    self.status_info.append('warning_certifications')
                if self.app.preferences['notifications'] and\
                        self.account.notifications['warning_certifications'][1]+24*3600 < time.time():
                    toast.display(self.tr("Certifications number"),
                              self.tr("<b>Warning : You are certified by only {0} persons, need {1}</b>")
                              .format(len(certifiers_of),
                                     parameters['sigQty']))
                    self.account.notifications['warning_certifications'][1] = time.time()

        except MembershipNotFoundError as e:
            pass
        except NoPeerAvailable:
            logging.debug("No peer available")
        self.refresh_data()

    def refresh_data(self):
        """
        Refresh data
        """
        self.tab_history.refresh_balance()
        self.refresh_status()

    @once_at_a_time
    @asyncify
    async def refresh_status(self):
        """
        Refresh status bar
        """
        logging.debug("Refresh status")
        if self.community:
            text = ""

            current_block_number = self.community.network.current_blockUID.number
            if current_block_number:
                text += self.tr("Block {0}").format(current_block_number)
                try:
                    block = await self.community.get_block(current_block_number)
                    text += " ({0})".format(QLocale.toString(
                                QLocale(),
                                QDateTime.fromTime_t(block['medianTime']),
                                QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                            ))
                except NoPeerAvailable as e:
                    logging.debug(str(e))
                    text += " ( ### ) "
                except errors.DuniterError as e:
                    if e.ucode == errors.BLOCK_NOT_FOUND:
                        logging.debug(str(e))

            if len(self.community.network.synced_nodes) == 0:
                self.button_membership.setEnabled(False)
                self.button_certification.setEnabled(False)
                self.button_send_money.setEnabled(False)
            else:
                self.button_send_money.setEnabled(True)
                self.refresh_quality_buttons()

            if self.community.network.quality > 0.66:
                icon = ':/icons/connected'
            elif self.community.network.quality > 0.33:
                icon = ':/icons/weak_connect'
            else:
                icon = ':/icons/disconnected'

            status_infotext = " - ".join([self.account.notifications[info][0] for info in self.status_info])
            label_text = text
            if status_infotext != "":
                label_text += " - {0}".format(status_infotext)

            self.status_label.setText(label_text)
            self.label_icon.setPixmap(QPixmap(icon).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def showEvent(self, event):
        self.refresh_status()

    def referential_changed(self):
        if self.community and self.tab_history.ui.table_history.model():
            self.tab_history.ui.table_history.model().sourceModel().refresh_transfers()
            self.tab_history.refresh_balance()
            self.tab_informations.refresh()

    def retranslateUi(self, widget):
        """
        Method to complete translations missing from generated code
        :param widget:
        :return:
        """
        self.tabs.setTabText(self.tabs.indexOf(self.tab_wot.widget), self.tr(CommunityWidget._tab_wot_label))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_network), self.tr(CommunityWidget._tab_network_label))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_informations), self.tr(CommunityWidget._tab_informations_label))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_history.widget), self.tr(CommunityWidget._tab_history_label))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_identities.widget), self.tr(CommunityWidget._tab_identities_label))
        super().retranslateUi(self)

    def showEvent(self, QShowEvent):
        """

        :param QShowEvent:
        :return:
        """
        self.refresh_status()
        super().showEvent(QShowEvent)

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
