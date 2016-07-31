from PyQt5.QtCore import QLocale, pyqtSlot, QDateTime, QTimer
from ..agent.controller import AgentController
from .model import StatusBarModel
from .view import StatusBarView
import logging


class StatusBarController(AgentController):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation agent

        :param sakia.gui.status_bar.view.StatusBarView view: the presentation
        :param sakia.core.status_bar.model.StatusBarModel model: the model
        """
        super().__init__(parent, view, model)
        view.combo_referential.currentIndexChanged[int].connect(self.referential_changed)
        self.update_time()

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation agent
        :param sakia.gui.main_window.controller.MainWindowController parent:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = StatusBarView(parent.view)

        model = StatusBarModel(None, app)
        status_bar = cls(parent, view, model)
        model.setParent(status_bar)
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

        if self.model.account is None:
            self.view.combo_referential.setEnabled(False)
            self.view.status_label.setText(self.tr(""))
        else:
            self.view.combo_referential.blockSignals(True)
            self.view.combo_referential.clear()
            for ref in self.model.referentials():
                self.view.combo_referential.addItem(ref.translated_name())
            logging.debug(self.app.preferences)

            self.view.combo_referential.setEnabled(True)
            self.view.combo_referential.blockSignals(False)
            self.view.combo_referential.setCurrentIndex(self.app.preferences['ref'])

    @pyqtSlot(int)
    def referential_changed(self, index):
        if self.model.account:
            self.model.account.set_display_referential(index)