from PyQt5.QtCore import QObject


class AgentModel(QObject):
    """
    An agent
    """

    def __init__(self, parent):
        """
        Constructor of an agent

        :param sakia.core.gui.agent.controller.AbstractAgentController controller: the controller
        """
        super().__init__(parent)

    @property
    def account(self):
        return self.app.current_account
