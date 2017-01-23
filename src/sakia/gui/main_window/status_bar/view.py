from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QLabel, QComboBox
from PyQt5.QtCore import Qt


class StatusBarView(QStatusBar):
    """
    The model of Navigation component
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.label_icon = QLabel("", parent)

        self.status_label = QLabel("", parent)
        self.status_label.setTextFormat(Qt.RichText)

        self.label_time = QLabel("", parent)

        self.combo_referential = QComboBox(parent)

        self.addPermanentWidget(self.label_icon, 1)
        self.addPermanentWidget(self.status_label, 2)
        self.addPermanentWidget(self.label_time)
        self.addPermanentWidget(self.combo_referential)
