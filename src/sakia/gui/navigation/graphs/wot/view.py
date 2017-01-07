from ..base.view import BaseGraphView
from .wot_tab_uic import Ui_WotWidget
from sakia.gui.widgets.busy import Busy
from PyQt5.QtCore import QEvent


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
        self.busy = Busy(self.graphics_view)
        self.busy.hide()

    def set_search_user(self, search_user):
        """
        Set the search user view in the gui
        :param sakia.gui.search_user.view.SearchUserView search_user: the view
        :return:
        """
        self.layout().insertWidget(0, search_user)

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

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)
