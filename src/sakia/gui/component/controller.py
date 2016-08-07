from PyQt5.QtCore import QObject


class ComponentController(QObject):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param PyQt5.QtWidgets.QWidget view: the presentation
        :param sakia.gui.component.model.ComponentModel model: the model
        """
        super().__init__(parent)
        self._view = view
        self._model = model

    @property
    def view(self):
        raise NotImplementedError("View property not implemented")

    @property
    def model(self):
        raise NotImplementedError("Model property not implemented")


    @classmethod
    def create(cls, parent, app, **kwargs):
        raise NotImplementedError("Create method not implemented")

    def attach(self, controller):
        """
        Attach an component controller to this controller
        :param ComponentController controller: the attached controller
        :return: the attached controller
        :rtype: ComponentController
        """
        if controller:
            controller.setParent(self)
            return controller
        else:
            return None
