from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QEvent


class BaseGraphView(QWidget):
    """
    Base graph view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super().changeEvent(event)