from sakia.gui.agent.model import AgentModel


class MainWindowModel(AgentModel):
    """
    The model of Navigation agent
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

