from PyQt5.QtCore import QLocale, pyqtSlot, QDateTime, QTimer, QObject
from .model import StatusBarModel
from .view import StatusBarView
import logging


class StatusBarController(QObject):
    """
    The navigation panel
    """

    def __init__(self, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.status_bar.view.StatusBarView view: the presentation
        :param sakia.core.status_bar.model.StatusBarModel model: the model
        """
        super().__init__()
        self.view = view
        self.model = model
        view.combo_referential.currentIndexChanged[int].connect(self.referential_changed)
        self.update_time()

    @classmethod
    def create(cls, app, **kwargs):
        """
        Instanciate a navigation component
        :param sakia.gui.main_window.controller.MainWindowController parent:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = StatusBarView(None)

        model = StatusBarModel(None, app)
        status_bar = cls(view, model)
        return status_bar

    @pyqtSlot()
    def update_time(self):
        dateTime = QDateTime.currentDateTime()
        self.view.label_time.setText("{0}".format(QLocale.toString(
                        QLocale(),
                        QDateTime.currentDateTime(),
                        QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                    )))
        timer = QTimer()
        timer.timeout.connect(self.update_time)
        timer.start(1000)

    def refresh(self):
        """
        Refresh main window
        When the selected account changes, all the widgets
        in the window have to be refreshed
        """
        logging.debug("Refresh started")
        for ref in self.model.referentials():
            self.view.combo_referential.addItem(ref.translated_name())

        self.view.combo_referential.setCurrentIndex(self.model.default_referential())

    @pyqtSlot(int)
    def referential_changed(self, index):
        pass