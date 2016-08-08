from PyQt5.QtCore import QEvent
from ..base.view import BaseGraphView
from .explorer_uic import Ui_ExplorerWidget


class ExplorerView(BaseGraphView, Ui_ExplorerWidget):
    """
    Wot graph view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)

    def set_steps_max(self, maximum):
        """
        Set the steps slider max value
        :param int maximum: the max value
        """
        self.steps_slider.setMaximum(maximum)

    def scene(self):
        """
        Get the scene of the underlying graphics view
        :return:
        """
        return self.graphics_view.scene()

    def reset_steps(self):
        """
        Reset the steps slider
        """
        self.steps_slider.setValue(0)

    def steps(self):
        """
        Get the number of steps selected
        :return:
        """
        return self.steps_slider.value()

    def update_wot(self, nx_graph, identity):
        """
        Display given wot around given identity
        :param nx_graph:
        :param identity:
        :param steps:
        :return:
        """
        # draw graph in qt scene
        self.scene().update_wot(nx_graph, identity, self.steps_slider.maximum())
