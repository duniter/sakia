from PyQt5.QtWidgets import QTreeView
from .model import NavigationModel
from ..agent.controller import AgentController
from ..agent.model import AgentModel


class NavigationController(AgentController):
    """
    The navigation panel
    """

    def __init__(self, parent, presentation, model):
        """
        Constructor of the navigation agent

        :param PyQt5.QtWidgets.QTreeView presentation: the presentation
        :param sakia.core.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent, presentation, model)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation agent
        :param sakia.gui.agent.controller.AgentController parent:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        presentation = QTreeView(parent.presentation)
        model = NavigationModel(None, app)
        navigation = cls(presentation, model)
        model.setParent(navigation)
        return navigation

