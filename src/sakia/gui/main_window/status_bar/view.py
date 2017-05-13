from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QLabel, QComboBox, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QSize


class StatusBarView(QStatusBar):
    """
    The model of Navigation component
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.status_label = QLabel("", parent)
        self.status_label.setTextFormat(Qt.RichText)

        self.label_time = QLabel("", parent)

        self.combo_referential = QComboBox(parent)
        self.movie_loader = QMovie(":/icons/loader")
        self.label_loading = QLabel(parent)
        self.label_loading.setMovie(self.movie_loader)
        self.label_loading.setMaximumHeight(self.height())
        self.movie_loader.setScaledSize(QSize(16, 16))
        self.movie_loader.start()
        self.movie_loader.setPaused(True)
        self.addPermanentWidget(self.label_loading)
        self.addPermanentWidget(self.status_label, 2)
        self.addPermanentWidget(self.label_time)
        self.addPermanentWidget(self.combo_referential)

    def start_loading(self):
        self.movie_loader.setPaused(False)

    def stop_loading(self):
        self.movie_loader.setPaused(True)
