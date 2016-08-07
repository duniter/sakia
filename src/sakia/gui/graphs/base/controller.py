from ...component.controller import ComponentController
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QCursor
from sakia.tools.decorators import asyncify, once_at_a_time
from .view import BaseGraphView
from .model import BaseGraphModel
from ...widgets.context_menu import ContextMenu


class BaseGraphController(ComponentController):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model, password_asker):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent, view, model)
        self.password_asker = password_asker

    def set_scene(self, scene):
        """
        Set the scene and connects the signals
        :param sakia.gui.views.scenes.base_scene.BaseScene scene: the scene
        :return:
        """
        # add scene events
        scene.node_context_menu_requested.connect(self.node_context_menu)
        scene.node_clicked.connect(self.handle_node_click)

    @pyqtSlot(str, dict)
    def handle_node_click(self, pubkey, metadata):
        identity = self.model.get_identity_from_data(metadata, pubkey)
        self.draw_graph(identity)

    async def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Graph node identity
        """
        raise NotImplementedError("draw_graph not implemented")

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        raise NotImplementedError("reset not implemented")

    @once_at_a_time
    @asyncify
    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        raise NotImplementedError("refresh not implemented")

    @asyncify
    async def node_context_menu(self, pubkey):
        """
        Open the node context menu
        :param str pubkey: the pubkey of the node to open
        """
        identity = await self.model.get_identity(pubkey)
        menu = ContextMenu.from_data(self.view, self.model.app, self.model.account, self.model.community, self.password_asker,
                                     (identity,))
        menu.view_identity_in_wot.connect(self.draw_graph)

        # Show the context menu.
        menu.qmenu.popup(QCursor.pos())
