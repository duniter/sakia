from PyQt5.QtCore import QObject
from sakia.money import Referentials


class StatusBarModel(QObject):
    """
    The model of status bar component
    """

    def __init__(self, parent, app):
        """
        The status bar model
        :param parent:
        :param sakia.app.Application app: the app
        """
        super().__init__(parent)
        self.app = app

    def referentials(self):
        return Referentials

    def default_referential(self):
        return self.app.parameters.referential
