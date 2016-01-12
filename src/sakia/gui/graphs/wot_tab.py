import logging
import asyncio

from PyQt5.QtCore import QEvent, pyqtSignal, QT_TRANSLATE_NOOP
from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ...core.graph import WoTGraph
from ...gen_resources.wot_tab_uic import Ui_WotTabWidget
from ...gui.widgets.busy import Busy
from .graph_tab import GraphTabWidget


class WotTabWidget(GraphTabWidget, Ui_WotTabWidget):

    money_sent = pyqtSignal()

    def __init__(self, app):
        """
        :param sakia.core.app.Application app: Application instance
        """
        super().__init__(app)
        # construct from qtDesigner
        self.setupUi(self)
        self.search_user_widget.init(app)
        self.busy = Busy(self.graphicsView)
        self.busy.hide()

        self.set_scene(self.graphicsView.scene())

        self.account = None
        self.community = None
        self.password_asker = None
        self.app = app
        self.draw_task = None

        self.search_user_widget.identity_selected.connect(self.draw_graph)
        self.search_user_widget.reset.connect(self.reset)

        # create node metadata from account
        self._current_identity = None

    def cancel_once_tasks(self):
        cancel_once_task(self, self.draw_graph)
        cancel_once_task(self, self.refresh_informations_frame)
        cancel_once_task(self, self.reset)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()
        self.search_user_widget.change_account(account)
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self.cancel_once_tasks()
        self.search_user_widget.change_community(community)
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
