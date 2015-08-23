# -*- coding: utf-8 -*-

import logging
from cutecoin.core.graph import Graph
from PyQt5.QtWidgets import QWidget, QComboBox, QLineEdit
from PyQt5.QtCore import pyqtSlot
from cutecoin.core.net.api import bma
from cutecoin.core.registry import BlockchainState
from ..gen_resources.wot_tab_uic import Ui_WotTabWidget
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, \
    ARC_STATUS_WEAK


class WotTabWidget(QWidget, Ui_WotTabWidget):
    def __init__(self, app, account, community, password_asker, parent=None):
        """
        :param cutecoin.core.app.Application app:   Application instance
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param QWidget parent: Parent
        :return:
        """
        super().__init__(parent)
        self.parent = parent

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

        self.account = account
        self.community = community
        self.password_asker = password_asker
        self.app = app

        # nodes list for menu from search
        self.nodes = list()

        # create node metadata from account
        self._current_identity = None
        self.draw_graph(self.account.identity(self.community))
        self.community.network.new_block_mined.connect(self.refresh)

    @pyqtSlot(dict)
    def handle_node_click(self, metadata):
        self.draw_graph(
            self.app.identities_registry.from_handled_data(
                metadata['text'],
                metadata['id'],
                BlockchainState.VALIDATED
            )
        )

    def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param cutecoin.core.registry.Identity identity: Graph node identity
        """
        logging.debug("Draw graph - " + identity.uid)

        identity_account = self.account.identity(self.community)

        # Disconnect old identity
        try:
            if self._current_identity and self._current_identity != identity:
                self._current_identity.inner_data_changed.disconnect(self.handle_identity_change)
        except TypeError as e:
            if "disconnect()" in str(e):
                logging.debug("Disconnect of old identity failed.")

        #Connect new identity
        if self._current_identity != identity:
            self._current_identity = identity
            identity.inner_data_changed.connect(self.handle_identity_change)

        # create Identity from node metadata
        certifier_list = identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        certified_list = identity.unique_valid_certified_by(self.app.identities_registry, self.community)

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
        self.draw_graph(
            self.account.identity(self.community)
        )

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        self.draw_graph(self._current_identity)

    @pyqtSlot(str)
    def handle_identity_change(self, request):
        self.refresh()

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
