import asyncio

from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QCursor

from sakia.decorators import asyncify, once_at_a_time
from sakia.gui.widgets.context_menu import ContextMenu


class BaseGraphController(QObject):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model, password_asker):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
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
        asyncio.ensure_future(self.draw_graph(metadata['identity']))

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

    def node_context_menu(self, identity):
        """
        Open the node context menu
        :param sakia.data.entities.Identity identity: the identity of the node to open
        """
        menu = ContextMenu.from_data(self.view, self.model.app, None, (identity,))
        menu.view_identity_in_wot.connect(self.draw_graph)

        # Show the context menu.
        menu.qmenu.popup(QCursor.pos())
