from PyQt5.QtCore import QObject


class HomeScreenModel(QObject):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    @property
    def account(self):
        return self.app.current_account