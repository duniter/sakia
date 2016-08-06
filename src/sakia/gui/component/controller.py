from PyQt5.QtCore import QObject


class ComponentController(QObject):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param PyQt5.QtWidgets.QWidget view: the presentation
        :param sakia.core.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model

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
