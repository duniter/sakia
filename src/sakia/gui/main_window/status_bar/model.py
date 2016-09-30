import logging

from sakia.gui.component.model import ComponentModel
from sakia.money import Referentials


class StatusBarModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    @property
    def account(self):
        return self.app.current_account

    def referentials(self):
        return Referentials

    def default_referential(self):
        logging.debug(self.app.preferences)
        return self.app.preferences['ref']