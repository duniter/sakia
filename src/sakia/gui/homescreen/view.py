from PyQt5.QtWidgets import QWidget
from .homescreen_uic import Ui_HomescreenWidget


class HomeScreenView(QWidget, Ui_HomescreenWidget):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
