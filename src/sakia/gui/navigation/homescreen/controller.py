from PyQt5.QtCore import QObject
from .view import HomeScreenView
from .model import HomeScreenModel


class HomeScreenController(QObject):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model

    @classmethod
    def create(cls, parent, app):
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
