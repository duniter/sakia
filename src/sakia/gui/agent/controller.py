from PyQt5.QtCore import QObject


class AgentController(QObject):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation agent

        :param PyQt5.QtWidgets.QWidget presentation: the presentation
        :param sakia.core.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model

    def attach(self, controller):
        """
        Attach an agent controller to this controller
        :param AgentController controller: the attached controller
        :return: the attached controller
        :rtype: AgentController
        """
        if controller:
            controller.setParent(self)
            return controller
        else:
            return None
