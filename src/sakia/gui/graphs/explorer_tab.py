import logging

from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtWidgets import QWidget

from ...tools.exceptions import NoPeerAvailable
from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ...core.graph import ExplorerGraph
from .graph_tab import GraphTabWidget
from ...gen_resources.explorer_tab_uic import Ui_ExplorerTabWidget


class ExplorerTabWidget(GraphTabWidget, Ui_ExplorerTabWidget):

    money_sent = pyqtSignal()

    def __init__(self, app, account=None, community=None, password_asker=None,
                 widget=QWidget, view=Ui_ExplorerTabWidget):
        """
        :param sakia.core.app.Application app: Application instance
        :param sakia.core.app.Application app: Application instance
        :param sakia.core.Account account: The account displayed in the widget
        :param sakia.core.Community community: The community displayed in the widget
        :param sakia.gui.Password_Asker: password_asker: The widget to ask for passwords
        """
        # construct from qtDesigner
        super().__init__(app, account, community, password_asker, widget)
        self.ui = view()
        self.ui.setupUi(self.widget)
        self.ui.search_user_widget.init(app)

        self.set_scene(self.ui.graphicsView.scene())
        self.graph = None
        self.app = app
        self.draw_task = None

        # nodes list for menu from search
        self.nodes = list()

        # create node metadata from account
        self._current_identity = None
        self.ui.button_go.clicked.connect(self.go_clicked)
        self.ui.search_user_widget.identity_selected.connect(self.draw_graph)
        self.ui.search_user_widget.reset.connect(self.reset)

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_informations_frame)
        cancel_once_task(self, self.reset)

    def change_account(self, account, password_asker):
        self.ui.search_user_widget.change_account(account)
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self.community = community
        if self.graph:
            self.graph.stop_exploration()
        self.graph = ExplorerGraph(self.app, self.community)
        self.graph.graph_changed.connect(self.refresh)
        self.ui.search_user_widget.change_community(community)
        self.graph.current_identity_changed.connect(self.ui.graphicsView.scene().update_current_identity)
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

            self.graph.start_exploration(identity, self.ui.steps_slider.value())

            # draw graph in qt scene
            self.ui.graphicsView.scene().clear()
            self.ui.graphicsView.scene().update_wot(self.graph.nx_graph, identity, self.ui.steps_slider.maximum())

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        if self._current_identity:
            # draw graph in qt scene
            self.ui.graphicsView.scene().update_wot(self.graph.nx_graph, self._current_identity, self.ui.steps_slider.maximum())
        else:
            self.reset()

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        if self.account and self.community:
            try:
                parameters = await self.community.parameters()
                self.ui.steps_slider.setMaximum(parameters['stepMax'])
                self.ui.steps_slider.setValue(int(0.33 * parameters['stepMax']))
                identity = await self.account.identity(self.community)
                self.draw_graph(identity)
            except NoPeerAvailable:
                logging.debug("No peer available")

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
