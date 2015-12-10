# -*- coding: utf-8 -*-

import logging
import asyncio

from PyQt5.QtWidgets import QWidget, QComboBox, QDialog
from PyQt5.QtCore import pyqtSlot, QEvent, QLocale, QDateTime, pyqtSignal
from ucoinpy.api import bma

from ..tools.exceptions import MembershipNotFoundError
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..core.graph import Graph
from ..core.registry import BlockchainState
from .member import MemberDialog
from .certification import CertificationDialog
from .transfer import TransferMoneyDialog
from .contact import ConfigureContactDialog
from ..gen_resources.wot_tab_uic import Ui_WotTabWidget
from .views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, NODE_STATUS_OUT
from .widgets.busy import Busy
from ..tools.exceptions import NoPeerAvailable


class WotTabWidget(QWidget, Ui_WotTabWidget):

    money_sent = pyqtSignal()

    def __init__(self, app):
        """
        :param sakia.core.app.Application app: Application instance
        """
        super().__init__()
        # construct from qtDesigner
        self.setupUi(self)

        # Default text when combo lineEdit is empty
        self.comboBoxSearch.lineEdit().setPlaceholderText(self.tr('Research a pubkey, an uid...'))
        #  add combobox events
        self.comboBoxSearch.lineEdit().returnPressed.connect(self.search)
        # To fix a recall of the same item with different case,
        # the edited text is not added in the item list
        self.comboBoxSearch.setInsertPolicy(QComboBox.NoInsert)

        self.busy = Busy(self.graphicsView)
        self.busy.hide()

        # add scene events
        self.graphicsView.scene().node_clicked.connect(self.handle_node_click)
        self.graphicsView.scene().node_signed.connect(self.sign_node)
        self.graphicsView.scene().node_transaction.connect(self.send_money_to_node)
        self.graphicsView.scene().node_contact.connect(self.add_node_as_contact)
        self.graphicsView.scene().node_member.connect(self.identity_informations)
        self.graphicsView.scene().node_copy_pubkey.connect(self.copy_node_pubkey)

        self.account = None
        self.community = None
        self.password_asker = None
        self.app = app
        self.draw_task = None

        # nodes list for menu from search
        self.nodes = list()

        # create node metadata from account
        self._current_identity = None

    def cancel_once_tasks(self):
        cancel_once_task(self, self.draw_graph)
        cancel_once_task(self, self.refresh_informations_frame)
        cancel_once_task(self, self.reset)

    def change_account(self, account, password_asker):
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self._auto_refresh(community)
        self.community = community
        self.reset()

    def _auto_refresh(self, new_community):
        if self.community:
            try:
                self.community.network.new_block_mined.disconnect(self.refresh)
            except TypeError as e:
                if "connected" in str(e):
                    logging.debug("new block mined not connected")
        if self.app.preferences["auto_refresh"]:
            if new_community:
                new_community.network.new_block_mined.connect(self.refresh)
            elif self.community:
                self.community.network.new_block_mined.connect(self.refresh)

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def refresh_informations_frame(self):
        parameters = self.community.parameters
        try:
            identity = yield from self.account.identity(self.community)
            membership = identity.membership(self.community)
            renew_block = membership['blockNumber']
            last_renewal = self.community.get_block(renew_block)['medianTime']
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            last_renewal = None
            expiration = None

        certified = yield from identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        certifiers = yield from identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        if last_renewal and expiration:
            date_renewal = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(last_renewal).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )
            date_expiration = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )

            if self.account.pubkey in self.community.members_pubkeys():
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Membership"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
            else:
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Not a member"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
        else:
            # set infos in label
            self.label_general.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.account.name, self.account.pubkey,
                    self.tr("Not a member"),
                    self.tr("Your web of trust"),
                    self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                         len(certified))
                )
            )

    @pyqtSlot(dict)
    def handle_node_click(self, metadata):
        self.draw_graph(
            self.app.identities_registry.from_handled_data(
                metadata['text'],
                metadata['id'],
                None,
                BlockchainState.VALIDATED,
                self.community
            )
        )

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Graph node identity
        """
        logging.debug("Draw graph - " + identity.uid)
        self.busy.show()

        if self.community:
            identity_account = yield from self.account.identity(self.community)

            #Connect new identity
            if self._current_identity != identity:
                self._current_identity = identity

            # create Identity from node metadata
            certifier_list = yield from identity.unique_valid_certifiers_of(self.app.identities_registry,
                                                                            self.community)
            certified_list = yield from identity.unique_valid_certified_by(self.app.identities_registry,
                                                                           self.community)

            # create empty graph instance
            graph = Graph(self.app, self.community)

            # add wallet node
            node_status = 0
            if identity == identity_account:
                node_status += NODE_STATUS_HIGHLIGHTED
            is_member = yield from identity.is_member(self.community)
            if is_member is False:
                node_status += NODE_STATUS_OUT
            node_status += NODE_STATUS_SELECTED
            graph.add_identity(identity, node_status)

            # populate graph with certifiers-of
            yield from graph.add_certifier_list(certifier_list, identity, identity_account)
            # populate graph with certified-by
            yield from graph.add_certified_list(certified_list, identity, identity_account)

            # draw graph in qt scene
            self.graphicsView.scene().update_wot(graph.get())

            # if selected member is not the account member...
            if identity.pubkey != identity_account.pubkey:
                # add path from selected member to account member
                path = yield from graph.get_shortest_path_between_members(identity, identity_account)
                if path:
                    self.graphicsView.scene().update_path(path)
        self.busy.hide()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        if self.account and self.community:
            identity = yield from self.account.identity(self.community)
            self.draw_graph(identity)

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        if self._current_identity:
            self.draw_graph(self._current_identity)
        else:
            self.reset()

    @asyncify
    @asyncio.coroutine
    def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        text = self.comboBoxSearch.lineEdit().text()

        if len(text) < 2:
            return False
        try:
            response = yield from self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})

            nodes = {}
            for identity in response['results']:
                nodes[identity['pubkey']] = identity['uids'][0]['uid']

            if nodes:
                self.nodes = list()
                self.comboBoxSearch.clear()
                self.comboBoxSearch.lineEdit().setText(text)
                for pubkey, uid in nodes.items():
                    self.nodes.append({'pubkey': pubkey, 'uid': uid})
                    self.comboBoxSearch.addItem(uid)
                self.comboBoxSearch.showPopup()
        except NoPeerAvailable:
            pass

    def select_node(self, index):
        """
        Select node in graph when item is selected in combobox
        """
        if index < 0 or index >= len(self.nodes):
            return False
        node = self.nodes[index]
        metadata = {'id': node['pubkey'], 'text': node['uid']}
        self.draw_graph(
            self.app.identities_registry.from_handled_data(
                metadata['text'],
                metadata['id'],
                None,
                BlockchainState.VALIDATED,
                self.community
            )
        )

    def identity_informations(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        dialog = MemberDialog(self.app, self.account, self.community, identity)
        dialog.exec_()

    @asyncify
    @asyncio.coroutine
    def sign_node(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        yield from CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    @asyncify
    @asyncio.coroutine
    def send_money_to_node(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        result = yield from TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        if result == QDialog.Accepted:
            self.money_sent.emit()

    def copy_node_pubkey(self, metadata):
        cb = self.app.qapp.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(metadata['id'], mode=cb.Clipboard)

    def add_node_as_contact(self, metadata):
        # check if contact already exists...
        if metadata['id'] == self.account.pubkey \
                or metadata['id'] in [contact['pubkey'] for contact in self.account.contacts]:
            return False
        dialog = ConfigureContactDialog(self.account, self.window(), {'name': metadata['text'],
                                                                      'pubkey': metadata['id'],
                                                                      })
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self._auto_refresh(None)
            self.refresh()
        return super(WotTabWidget, self).changeEvent(event)
