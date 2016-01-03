import logging
import asyncio

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import QEvent, pyqtSignal, QT_TRANSLATE_NOOP
from ucoinpy.api import bma

from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ...core.graph import WoTGraph
from ...gen_resources.wot_tab_uic import Ui_WotTabWidget
from ...gui.widgets.busy import Busy
from ...tools.exceptions import NoPeerAvailable
from .graph_tab import GraphTabWidget


class WotTabWidget(GraphTabWidget, Ui_WotTabWidget):

    money_sent = pyqtSignal()
    _search_placeholder = QT_TRANSLATE_NOOP("WotTabWidget", "Research a pubkey, an uid...")

    def __init__(self, app):
        """
        :param sakia.core.app.Application app: Application instance
        """
        super().__init__(app)
        # construct from qtDesigner
        self.setupUi(self)

        # Default text when combo lineEdit is empty
        self.comboBoxSearch.lineEdit().setPlaceholderText(self.tr(WotTabWidget._search_placeholder))
        #  add combobox events
        self.comboBoxSearch.lineEdit().returnPressed.connect(self.search)
        # To fix a recall of the same item with different case,
        # the edited text is not added in the item list
        self.comboBoxSearch.setInsertPolicy(QComboBox.NoInsert)

        self.busy = Busy(self.graphicsView)
        self.busy.hide()

        self.set_scene(self.graphicsView.scene())

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
        self.cancel_once_tasks()
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self.cancel_once_tasks()
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
    async def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Center identity
        """
        logging.debug("Draw graph - " + identity.uid)
        self.busy.show()

        if self.community:
            identity_account = await self.account.identity(self.community)

            # create empty graph instance
            graph = WoTGraph(self.app, self.community)
            await graph.initialize(identity, identity_account)
            # draw graph in qt scene
            self.graphicsView.scene().update_wot(graph.nx_graph, identity)

            # if selected member is not the account member...
            if identity.pubkey != identity_account.pubkey:
                # add path from selected member to account member
                path = await graph.get_shortest_path_to_identity(identity_account, identity)
                if path:
                    self.graphicsView.scene().update_path(graph.nx_graph, path)
        self.busy.hide()

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        if self.account and self.community:
            identity = await self.account.identity(self.community)
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
    async def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        text = self.comboBoxSearch.lineEdit().text()

        if len(text) < 2:
            return False
        try:
            response = await self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})

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

    def retranslateUi(self, widget):
        """
        Retranslate missing widgets from generated code
        """
        self.comboBoxSearch.lineEdit().setPlaceholderText(self.tr(WotTabWidget._search_placeholder))
        super().retranslateUi(self)

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
