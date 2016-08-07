from PyQt5.QtCore import QEvent
from ..base.view import BaseGraphView
from .wot_tab_uic import Ui_WotWidget


class WotView(BaseGraphView, Ui_WotWidget):
    """
    Wot graph view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)

    def scene(self):
        """
        Get the scene of the underlying graphics view
        :return:
        """
        return self.graphics_view.scene()

    def display_wot(self, nx_graph, identity):
        """
        Display given wot around given identity
        :param nx_graph:
        :param identity:
        :return:
        """
        # draw graph in qt scene
        self.graphics_view.scene().update_wot(nx_graph, identity)

    def display_path(self, nx_graph, path):
        """
        Display given path
        :param nx_graph:
        :param path:
        :return:
        """
        self.ui.graphicsView.scene().update_path(nx_graph, path)
