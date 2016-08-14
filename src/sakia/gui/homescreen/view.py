from PyQt5.QtWidgets import QWidget
from .homescreen_uic import Ui_HomescreenWidget


class HomeScreenView(QWidget, Ui_HomescreenWidget):
    """
    classdocs
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)
