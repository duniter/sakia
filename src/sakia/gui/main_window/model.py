from PyQt5.QtCore import QObject


class MainWindowModel(QObject):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

