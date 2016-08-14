from ..component.controller import ComponentController
from .view import HomeScreenView
from .model import HomeScreenModel


class HomeScreenController(ComponentController):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent, view, model)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a homescreen component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new Homescreen controller
        :rtype: HomeScreenController
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