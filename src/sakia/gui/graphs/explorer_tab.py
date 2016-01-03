import logging

from PyQt5.QtCore import QEvent, pyqtSignal, QT_TRANSLATE_NOOP

from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ...core.graph import ExplorerGraph
from .graph_tab import GraphTabWidget
from ...gen_resources.explorer_tab_uic import Ui_ExplorerTabWidget


class ExplorerTabWidget(GraphTabWidget, Ui_ExplorerTabWidget):

    money_sent = pyqtSignal()

    _search_placeholder = QT_TRANSLATE_NOOP("ExplorerTabWidget", "Research a pubkey, an uid...")

    def __init__(self, app):
        """
        :param sakia.core.app.Application app: Application instance
        """
        # construct from qtDesigner
        super().__init__(app)
        self.setupUi(self)
        self.set_scene(self.graphicsView.scene())

        self.account = None
        self.community = None
        self.password_asker = None
        self.graph = None
        self.app = app
        self.draw_task = None

        # nodes list for menu from search
        self.nodes = list()

        # create node metadata from account
        self._current_identity = None
        self.button_go.clicked.connect(self.go_clicked)

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_informations_frame)
        cancel_once_task(self, self.reset)

    def change_account(self, account, password_asker):
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self.community = community
        if self.graph:
            self.graph.stop_exploration()
        self.graph = ExplorerGraph(self.app, self.community)
        self.graph.graph_changed.connect(self.refresh)
        self.reset()

    def go_clicked(self):
        if self.graph:
            self.graph.stop_exploration()
            self.draw_graph(self._current_identity)

    def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Graph node identity
        """
        logging.debug("Draw graph - " + identity.uid)

        if self.community:
            #Connect new identity
            if self._current_identity != identity:
                self._current_identity = identity

            self.graph.start_exploration(identity, self.steps_slider.value())

            # draw graph in qt scene
            self.graphicsView.scene().update_wot(self.graph.nx_graph, identity, self.steps_slider.maximum())

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        if self._current_identity:
            # draw graph in qt scene
            self.graphicsView.scene().update_wot(self.graph.nx_graph, self._current_identity, self.steps_slider.maximum())
        else:
            self.reset()

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        if self.account and self.community:
            parameters = await self.community.parameters()
            self.steps_slider.setMaximum(parameters['stepMax'])
            self.steps_slider.setValue(int(0.33 * parameters['stepMax']))
            identity = await self.account.identity(self.community)
            self.draw_graph(identity)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super().changeEvent(event)
