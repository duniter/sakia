from PyQt5.QtWidgets import QFrame, QSizePolicy
from PyQt5.QtCore import QModelIndex
from .navigation_uic import Ui_Navigation
from ...models.generic_tree import GenericTreeModel


class NavigationView(QFrame, Ui_Navigation):
    """
    The view of navigation panel
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.tree_view.clicked.connect(self.handle_click)

    def set_model(self, model):
        """
        Change the navigation pane
        :param sakia.gui.navigation.model.NavigationModel
        """
        self.tree_view.setModel(model.generic_tree())

    def add_widget(self, widget):
        """
        Add a widget to the stacked_widget
        :param PyQt5.QtWidgets.QWidget widget: the new widget
        """
        self.stacked_widget.addWidget(widget)
        return widget

    def handle_click(self, index):
        """
        Click on the navigation pane
        :param PyQt5.QtCore.QModelIndex index: the index
        :return:
        """
        if index.isValid():
            raw_data = self.tree_view.model().data(index, GenericTreeModel.ROLE_RAW_DATA)
            widget = raw_data['widget']
            if self.stacked_widget.indexOf(widget):
                self.stacked_widget.setCurrentWidget(widget)