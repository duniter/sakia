"""
Created on 2 févr. 2014

@author: inso
"""

import logging
import asyncio
import time

from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QPushButton, QTabBar, QAction
from PyQt5.QtCore import pyqtSlot, QDateTime, QLocale, QEvent

from PyQt5.QtGui import QIcon

from .wot_tab import WotTabWidget
from .identities_tab import IdentitiesTabWidget
from .transactions_tab import TransactionsTabWidget
from .network_tab import NetworkTabWidget
from .informations_tab import InformationsTabWidget
from cutecoin.gui.widgets.dialogs import QAsyncMessageBox
from cutecoin.gui.widgets import toast
from ..tools.exceptions import MembershipNotFoundError, LookupFailureError, NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
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
        self.account = None
        self.community = None
        self.password_asker = None
        self.status_label = status_label

        self.status_info = []

        super().setupUi(self)

        self.tab_wot = WotTabWidget(self.app)

        self.tab_identities = IdentitiesTabWidget(self.app)

        self.tab_history = TransactionsTabWidget(self.app)

        self.tab_informations = InformationsTabWidget(self.app)

        self.tab_network = NetworkTabWidget(self.app)
        self.tab_identities.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_identities.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot))
        self.tab_history.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_history.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot))
        self.tab_identities.money_sent.connect(lambda: self.tab_history.table_history.model().sourceModel().refresh_transfers())
        self.tab_wot.money_sent.connect(lambda: self.tab_history.table_history.model().sourceModel().refresh_transfers())

        self.tabs.addTab(self.tab_history,
                                 QIcon(':/icons/tx_icon'),
                                self.tr("Transactions"))

        self.tabs.addTab(self.tab_wot,
                         QIcon(':/icons/wot_icon'),
                         self.tr("Web of Trust"))

        self.tabs.addTab(self.tab_identities,
                         QIcon(':/icons/members_icon'),
                         self.tr("Search Identities"))

        self.tabs.addTab(self.tab_network,
                                 QIcon(":/icons/network_icon"),
                                 self.tr("Network"))


        action_showinfo = QAction(self.tr("Show informations"), self.toolbutton_menu)

        def show_info():
            if self.tabs.indexOf(self.tab_informations) == -1:
                self.tabs.addTab(self.tab_informations,
                                         QIcon(":/icons/informations_icon"),
                                         self.tr("Informations"))
                style = self.app.qapp.style()
                icon = style.standardIcon(style.SP_DockWidgetCloseButton)
                close_button = QPushButton(icon, '')
                close_button.clicked.connect(lambda: self.tabs.removeTab(self.tabs.indexOf(self.tab_informations)))
                close_button.setStyleSheet('border-style: inset;')
                self.tabs.tabBar().setTabButton(4, QTabBar.RightSide, close_button)

        action_showinfo.triggered.connect(show_info)
        self.toolbutton_menu.addAction(action_showinfo)
        self.button_membership.clicked.connect(self.send_membership_demand)

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_block)
        cancel_once_task(self, self.refresh_status)
        cancel_once_task(self, self.refresh_quality_buttons)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()

        self.account = account

        self.password_asker = password_asker
        self.tab_wot.change_account(account, self.password_asker)
        self.tab_identities.change_account(account, self.password_asker)
        self.tab_history.change_account(account, self.password_asker)
        self.tab_informations.change_account(account)

    def change_community(self, community):
        self.cancel_once_tasks()

        self.tab_network.change_community(community)
        self.tab_wot.change_community(community)
        self.tab_history.change_community(community)
        self.tab_identities.change_community(community)
        self.tab_informations.change_community(community)

        if self.community:
            self.community.network.new_block_mined.disconnect(self.refresh_block)
            self.community.network.nodes_changed.disconnect(self.refresh_status)
        if community:
            community.network.new_block_mined.connect(self.refresh_block)
            community.network.nodes_changed.connect(self.refresh_status)
            self.label_currency.setText(community.currency)
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
    @asyncio.coroutine
    def refresh_block(self, block_number):
        """
        When a new block is found, start handling data.
        @param: block_number: The number of the block mined
        """
        logging.debug("Refresh block")
        self.status_info.clear()
        try:
            person = yield from self.app.identities_registry.future_find(self.app.current_account.pubkey, self.community)
            expiration_time = yield from person.membership_expiration_time(self.community)
            parameters = yield from self.community.parameters()
            sig_validity = parameters['sigValidity']
            warning_expiration_time = int(sig_validity / 3)
            will_expire_soon = (expiration_time < warning_expiration_time)

            logging.debug("Try")
            if will_expire_soon:
                days = int(expiration_time / 3600 / 24)
                if days > 0:
                    if 'membership_expire_soon' not in self.status_info:
                        self.status_info.append('membership_expire_soon')

                    if self.app.preferences['notifications'] and\
                            self.app.notifications['membership_expire_soon'][1] < time.time()+24*3600:
                        toast.display(self.tr("Membership expiration"),
                                  self.tr("<b>Warning : Membership expiration in {0} days</b>").format(days))
                        self.app.notifications['membership_expire_soon'][1] = time.time()

            certifiers_of = yield from person.unique_valid_certifiers_of(self.app.identities_registry,
                                                                         self.community)
            if len(certifiers_of) < parameters['sigQty']:
                if 'warning_certifications' not in self.status_info:
                    self.status_info.append('warning_certifications')
                if self.app.preferences['notifications'] and\
                        self.app.notifications['warning_certifications'][1] < time.time()+24*3600:
                    toast.display(self.tr("Certifications number"),
                              self.tr("<b>Warning : You are certified by only {0} persons, need {1}</b>")
                              .format(len(certifiers_of),
                                     parameters['sigQty']))
                    self.app.notifications['warning_certifications'][1] = time.time()

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
    @asyncio.coroutine
    def refresh_status(self):
        """
        Refresh status bar
        """
        logging.debug("Refresh status")
        if self.community:
            text = ""

            current_block_number = self.community.network.current_blockid.number
            if current_block_number:
                text += self.tr(" Block {0}").format(current_block_number)
                try:
                    block = yield from self.community.get_block(current_block_number)
                    text += " ({0})".format(QLocale.toString(
                                QLocale(),
                                QDateTime.fromTime_t(block['medianTime']),
                                QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                            ))
                except NoPeerAvailable as e:
                    logging.debug(str(e))
                    text += " ( ### ) "
                except ValueError as e:
                    logging.debug(str(e))

            if len(self.community.network.synced_nodes) == 0:
                self.button_membership.setEnabled(False)
                self.button_certification.setEnabled(False)
                self.button_send_money.setEnabled(False)
            else:
                self.button_membership.setEnabled(True)
                self.button_certification.setEnabled(True)
                self.button_send_money.setEnabled(True)

            if self.community.network.quality > 0.66:
                icon = '<img src=":/icons/connected" width="12" height="12"/>'
            elif self.community.network.quality > 0.33:
                icon = '<img src=":/icons/weak_connect" width="12" height="12"/>'
            else:
                icon = '<img src=":/icons/disconnected" width="12" height="12"/>'

            status_infotext = " - ".join([self.app.notifications[info][0] for info in self.status_info])
            label_text = "{0}{1}".format(icon, text)
            if status_infotext != "":
                label_text += " - {0}".format(status_infotext)

            if self.app.preferences['expert_mode']:
                try:
                    members_pubkeys = yield from self.community.members_pubkeys()
                    label_text += self.tr(" - Median fork window : {0}")\
                        .format(self.community.network.fork_window(members_pubkeys))
                except NoPeerAvailable as e:
                    logging.debug(str(e))
                    label_text += self.tr(" - Median fork window : {0}")\
                        .format("#")

            self.status_label.setText(label_text)

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def refresh_quality_buttons(self):
        if self.account and self.community:
            try:
                account_identity = yield from self.account.identity(self.community)
                published_uid = account_identity.published_uid(self.community)
                if published_uid:
                    logging.debug("UID Published")
                    is_member = account_identity.is_member(self.community)
                    if is_member:
                        self.button_membership.setText(self.tr("Renew membership"))
                        self.button_membership.show()
                        self.button_certification.show()
                    else:
                        logging.debug("Not a member")
                        self.button_membership.setText(self.tr("Send membership demand"))
                        self.button_membership.show()
                        if self.community.get_block(0) != None:
                            self.button_certification.hide()
                else:
                    logging.debug("UID not published")
                    self.button_membership.hide()
                    self.button_certification.hide()
            except LookupFailureError:
                self.button_membership.hide()
                self.button_certification.hide()

    def showEvent(self, event):
        self.refresh_status()

    def referential_changed(self):
        if self.community and self.tab_history.table_history.model():
            self.tab_history.table_history.model().sourceModel().refresh_transfers()
            self.tab_history.refresh_balance()
            self.tab_informations.refresh()

    @asyncify
    @asyncio.coroutine
    def send_membership_demand(self, checked=False):
        password = yield from self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return
        result = yield from self.account.send_membership(password, self.community, 'IN')
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
            else:
                yield from QAsyncMessageBox.information(self, self.tr("Membership"),
                                                        self.tr("Success sending Membership demand"))
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Membership"), result[1])
            else:
                yield from QAsyncMessageBox.critical(self, self.tr("Membership"),
                                                        result[1])

    @asyncify
    @asyncio.coroutine
    def send_membership_leaving(self):
        reply = yield from QAsyncMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return
            result = yield from self.account.send_membership(password, self.community, 'OUT')
            if result[0]:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), self.tr("Success sending Revoke demand"))
                else:
                    yield from QAsyncMessageBox.information(self, self.tr("Revoke"),
                                                            self.tr("Success sending Revoke demand"))
            else:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), result[1])
                else:
                    yield from QAsyncMessageBox.critical(self, self.tr("Revoke"),
                                                         result[1])

    def showEvent(self, QShowEvent):
        """

        :param QShowEvent:
        :return:
        """
        self.refresh_status()

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
