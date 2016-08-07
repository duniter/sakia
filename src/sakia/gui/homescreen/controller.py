from ..component.controller import ComponentController
from .view import HomeScreenView
from .model import HomeScreenModel


class HomeScreenController(ComponentController):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param PyQt5.QtWidgets.QWidget presentation: the presentation
        :param sakia.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent, view, model)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a homescreen component
        :param sakia.gui.agent.controller.AgentController parent:
        :return: a new Homescreen controller
        :rtype: NavigationController
        """
        view = HomeScreenView(parent.view)
        model = HomeScreenModel(None, app)
        homescreen = cls(parent, view, model)
        model.setParent(homescreen)
        return homescreen

    @property
    def view(self) -> HomeScreenView:
        return self._view

    @property
    def model(self) -> HomeScreenModel:
        return self._model