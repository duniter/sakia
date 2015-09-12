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
from .transactions_tab import TransactionsTabWidget
from .network_tab import NetworkTabWidget
from .password_asker import PasswordAskerDialog
from . import toast
import asyncio
from ..tools.exceptions import MembershipNotFoundError, LookupFailureError, NoPeerAvailable
from ..tools.decorators import asyncify
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
        self.status_infotext = {'membership_expire_soon':
                            self.tr("Warning : Your membership is expiring soon."),
                            'warning_certifications':
                            self.tr("Warning : Your could miss certifications soon.")
                            }

        super().setupUi(self)

        self.tab_wot = WotTabWidget(self.app)

        self.tab_identities = IdentitiesTabWidget(self.app)

        self.tab_history = TransactionsTabWidget(self.app)

        self.tab_network = NetworkTabWidget(self.app)
        self.tab_identities.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_identities.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot))
        self.tab_history.view_in_wot.connect(self.tab_wot.draw_graph)
        self.tab_history.view_in_wot.connect(lambda: self.tabs.setCurrentWidget(self.tab_wot))

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

        self.button_membership.clicked.connect(self.send_membership_demand)

    def change_account(self, account, password_asker):
        if self.account:
            self.account.broadcast_error.disconnect(self.handle_broadcast_error)
            self.account.membership_broadcasted.disconnect(self.handle_membership_broadcasted)
            self.account.selfcert_broadcasted.disconnect(self.handle_selfcert_broadcasted)

        self.account = account

        if self.account:
            self.account.broadcast_error.connect(self.handle_broadcast_error)
            self.account.membership_broadcasted.connect(self.handle_membership_broadcasted)
            self.account.selfcert_broadcasted.connect(self.handle_selfcert_broadcasted)

        self.password_asker = password_asker
        self.tab_wot.change_account(account, self.password_asker)
        self.tab_identities.change_account(account, self.password_asker)
        self.tab_history.change_account(account, self.password_asker)

    def change_community(self, community):
        self.tab_network.change_community(community)
        self.tab_wot.change_community(community)
        self.tab_history.change_community(community)
        self.tab_identities.change_community(community)

        if self.community:
            self.community.network.new_block_mined.disconnect(self.refresh_block)
            self.community.network.nodes_changed.disconnect(self.refresh_status)
        if community:
            community.network.new_block_mined.connect(self.refresh_block)
            community.network.nodes_changed.connect(self.refresh_status)
            self.label_currency.setText(community.currency)
        self.community = community
        self.refresh_quality_buttons()

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

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
                    self.status_info.append('membership_expire_soon')

                    if self.app.preferences['notifications']:
                        toast.display(self.tr("Membership expiration"),
                                  self.tr("<b>Warning : Membership expiration in {0} days</b>").format(days))

            certifiers_of = yield from person.unique_valid_certifiers_of(self.app.identities_registry,
                                                                         self.community)
            if len(certifiers_of) < parameters['sigQty']:
                self.status_info.append('warning_certifications')
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Certifications number"),
                              self.tr("<b>Warning : You are certified by only {0} persons, need {1}</b>")
                              .format(len(certifiers_of),
                                     parameters['sigQty']))

        except MembershipNotFoundError as e:
            pass

        self.tab_history.start_progress()
        self.refresh_data()

    def refresh_data(self):
        """
        Refresh data when the blockchain watcher finished handling datas
        """
        self.tab_history.refresh_balance()
        self.tab_identities.refresh_data()
        self.refresh_status()

    @asyncify
    @asyncio.coroutine
    def refresh_status(self):
        """
        Refresh status bar
        """
        logging.debug("Refresh status")
        if self.community:
            text = self.tr(" Block {0}").format(self.community.network.latest_block_number)

            block = yield from self.community.get_block(self.community.network.latest_block_number)
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
                        if self.community.get_block(0) != qtbma.blockchain.Block.null_value:
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

    def publish_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Publishing your UID can be canceled by Revoke UID.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            try:
                self.account.send_selfcert(password, self.community)
                toast.display(self.tr("UID Publishing"),
                              self.tr("Success publishing your UID"))
            except ValueError as e:
                QMessageBox.critical(self, self.tr("Publish UID error"),
                                  str(e))
            except NoPeerAvailable as e:
                QMessageBox.critical(self, self.tr("Network error"),
                                     self.tr("Couldn't connect to network : {0}").format(e),
                                     QMessageBox.Ok)
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Error"),
                                      "{0}".format(e),
                                      QMessageBox.Ok)

    def revoke_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                                 self.tr("""Are you sure ?
Revoking your UID can only success if it is not already validated by the network.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            asyncio.async(self.account.revoke(password, self.community))

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

    def handle_broadcast_error(self, error, strdata):
        if self.app.preferences['notifications']:
            toast.display(error, strdata)
        else:
            QMessageBox.error(error, strdata)

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
