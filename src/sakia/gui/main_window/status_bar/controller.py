from PyQt5.QtCore import QLocale, pyqtSlot, QDateTime, QTimer, QObject
from .model import StatusBarModel
from .view import StatusBarView
from sakia.data.processors import BlockchainProcessor
import logging


class StatusBarController(QObject):
    """
    The navigation panel
    """

    def __init__(self, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.main_window.status_bar.view.StatusBarView view: the presentation
        :param sakia.gui.main_window.status_bar.model.StatusBarModel model: the model
        """
        super().__init__()
        self.view = view
        self.model = model
        view.combo_referential.currentIndexChanged[int].connect(self.referential_changed)
        self.update_time()

    @classmethod
    def create(cls, app):
        """
        Instanciate a navigation component

        :param sakia.app.Application app:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = StatusBarView(None)

        model = StatusBarModel(None, app, BlockchainProcessor.instanciate(app))
        status_bar = cls(view, model)
        app.new_blocks_handled.connect(status_bar.new_blocks_handled)
        if app.connection_exists():
            status_bar.new_blocks_handled()
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

    def start_loading(self):
        self.view.start_loading()

    def stop_loading(self):
        self.view.stop_loading()

    def new_blocks_handled(self):
        current_block = self.model.current_block()
        current_time = self.model.current_time()
        str_time = QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(current_time),
                        QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                    )
        self.view.status_label.setText(self.tr("Blockchain sync : {0} BAT ({1})").format(str_time, str(current_block)[:15]))

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
        self.model.app.change_referential(index)