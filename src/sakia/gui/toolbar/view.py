from PyQt5.QtWidgets import QFrame
from .toolbar_uic import Ui_SakiaToolbar


class ToolbarView(QFrame, Ui_SakiaToolbar):
    """
    The model of Navigation agent
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
