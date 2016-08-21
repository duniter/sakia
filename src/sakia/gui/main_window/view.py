from PyQt5.QtWidgets import QMainWindow
from .mainwindow_uic import Ui_MainWindow


class MainWindowView(QMainWindow, Ui_MainWindow):
    """
    The model of Navigation component
    """

    def __init__(self):
        super().__init__(None)
        self.setupUi(self)
