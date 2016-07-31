from sakia.gui.agent.model import AgentModel
from sakia.core.money import Referentials
import logging

class StatusBarModel(AgentModel):
    """
    The model of Navigation agent
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def referentials(self):
        return Referentials

    def default_referential(self):
        logging.debug(self.app.preferences)
        return self.app.preferences['ref']