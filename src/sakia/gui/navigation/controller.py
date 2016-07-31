from PyQt5.QtWidgets import QTreeView
from .model import NavigationModel
from ..agent.controller import AgentController
from .view import NavigationView


class NavigationController(AgentController):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation agent

        :param PyQt5.QtWidgets.QTreeView view: the presentation
        :param sakia.core.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent, view, model)
        self.view.setModel(model.tree())

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation agent
        :param sakia.gui.agent.controller.AgentController parent:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = NavigationView(parent.view)
        model = NavigationModel(None, app)
        navigation = cls(parent, view, model)
        model.setParent(navigation)
        return navigation

