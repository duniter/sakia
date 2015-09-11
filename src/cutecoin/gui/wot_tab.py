# -*- coding: utf-8 -*-

import logging
import asyncio
from cutecoin.core.graph import Graph
from ..tools.exceptions import MembershipNotFoundError
from ..tools.decorators import asyncify
from PyQt5.QtWidgets import QWidget, QComboBox, QLineEdit
from PyQt5.QtCore import pyqtSlot, QEvent, QLocale, QDateTime
from cutecoin.core.net.api import bma
from cutecoin.core.registry import BlockchainState
from ..gen_resources.wot_tab_uic import Ui_WotTabWidget
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, \
    ARC_STATUS_WEAK


class WotTabWidget(QWidget, Ui_WotTabWidget):
    def __init__(self, app):
        """
        :param cutecoin.core.app.Application app:   Application instance
        :return:
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

        # add scene events
        self.graphicsView.scene().node_clicked.connect(self.handle_node_click)
        self.graphicsView.scene().node_signed.connect(self.sign_node)
        self.graphicsView.scene().node_transaction.connect(self.send_money_to_node)
        self.graphicsView.scene().node_contact.connect(self.add_node_as_contact)
        self.graphicsView.scene().node_member.connect(self.identity_informations)

        self.account = None
        self.community = None
        self.password_asker = None
        self.app = app

        # nodes list for menu from search
        self.nodes = list()

        # create node metadata from account
        self._current_identity = None

    def change_account(self, account, password_asker):
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        if self.community:
            self.community.network.new_block_mined.disconnect(self.refresh)
        if community:
            community.network.new_block_mined.connect(self.refresh)
        self.community = community
        self.reset()

    @asyncify
    @asyncio.coroutine
    def refresh_informations_frame(self):
        parameters = self.community.parameters
        try:
            identity = self.account.identity(self.community)
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
                BlockchainState.VALIDATED
            )
        )

    @asyncify
    @asyncio.coroutine
    def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param cutecoin.core.registry.Identity identity: Graph node identity
        """
        logging.debug("Draw graph - " + identity.uid)

        if self.community:
            identity_account = self.account.identity(self.community)

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
            if identity.is_member(self.community) is False:
                node_status += NODE_STATUS_OUT
            node_status += NODE_STATUS_SELECTED
            graph.add_identity(identity, node_status)

            # populate graph with certifiers-of
            graph.add_certifier_list(certifier_list, identity, identity_account)
            # populate graph with certified-by
            graph.add_certified_list(certified_list, identity, identity_account)

            # draw graph in qt scene
            self.graphicsView.scene().update_wot(graph.get())

            # if selected member is not the account member...
            if identity.pubkey != identity_account.pubkey:
                # add path from selected member to account member
                path = graph.get_shortest_path_between_members(identity, identity_account)
                if path:
                    self.graphicsView.scene().update_path(path)

    def reset(self):
        """
        Reset graph scene to wallet identity
        """
        if self.account:
            self.draw_graph(
                self.account.identity(self.community)
            )

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        if self._current_identity:
            self.draw_graph(self._current_identity)
        else:
            self.reset()

    def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        text = self.comboBoxSearch.lineEdit().text()

        if len(text) < 2:
            return False
        try:
            response = self.community.simple_request(bma.wot.Lookup, {'search': text})
        except Exception as e:
            logging.debug('bma.wot.Lookup request error : ' + str(e))
            return False

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
                BlockchainState.VALIDATED
            )
        )

    def identity_informations(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            BlockchainState.VALIDATED
        )
        self.parent.identity_informations(identity)

    def sign_node(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            BlockchainState.VALIDATED
        )
        self.parent.certify_identity(identity)

    def send_money_to_node(self, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            metadata['id'],
            BlockchainState.VALIDATED
        )
        self.parent.send_money_to_identity(identity)

    def add_node_as_contact(self, metadata):
        # check if contact already exists...
        if metadata['id'] == self.account.pubkey \
                or metadata['id'] in [contact['pubkey'] for contact in self.account.contacts]:
            return False
        self.parent.add_identity_as_contact({'name': metadata['text'],
                                             'pubkey': metadata['id']})

    def get_block_mediantime(self, number):
        try:
            block = self.community.get_block(number)
        except Exception as e:
            logging.debug('community.get_block request error : ' + str(e))
            return False
        return block.mediantime

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super(WotTabWidget, self).changeEvent(event)
