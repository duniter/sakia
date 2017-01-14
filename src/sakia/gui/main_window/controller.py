import logging

from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QEvent, pyqtSlot, QObject
from PyQt5.QtGui import QIcon

from ..password_asker import PasswordAskerDialog
from ...__init__ import __version__
from ..widgets import toast
from .view import MainWindowView
from .model import MainWindowModel
from .status_bar.controller import StatusBarController
from .toolbar.controller import ToolbarController
from ..navigation.controller import NavigationController


class MainWindowController(QObject):
    """
    classdocs
    """

    def __init__(self, view, model, password_asker, status_bar, toolbar, navigation):
        """
        Init
        :param MainWindowView view: the ui of the mainwindow component
        :param sakia.gui.main_window.model.MainWindowModel: the model of the mainwindow component
        :param sakia.gui.status_bar.controller.StatusBarController status_bar: the controller of the status bar component
        :param sakia.gui.toolbar.controller.ToolbarController toolbar: the controller of the toolbar component
        :param sakia.gui.navigation.contoller.NavigationController navigation: the controller of the navigation

        :param PasswordAsker password_asker: the password asker of the application
        :type: sakia.core.app.Application
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.view = view
        self.model = model
        self.initialized = False
        self.password_asker = password_asker
        self.status_bar = status_bar
        self.toolbar = toolbar
        self.navigation = navigation
        self.stacked_widgets = {}
        self.view.bottom_layout.insertWidget(0, self.navigation.view)
        self.view.top_layout.addWidget(self.toolbar.view)
        self.view.setStatusBar(self.status_bar.view)

        QApplication.setWindowIcon(QIcon(":/icons/sakia_logo"))

    @classmethod
    def create(cls, app, password_asker, status_bar, toolbar, navigation):
        """
        Instanciate a navigation component
        :param sakia.gui.status_bar.controller.StatusBarController status_bar: the controller of the status bar component
        :param sakia.gui.toolbar.controller.ToolbarController toolbar: the controller of the toolbar component
        :param sakia.gui.navigation.contoller.NavigationController navigation: the controller of the navigation

        :return: a new Navigation controller
        :rtype: MainWindowController
        """
        view = MainWindowView()
        model = MainWindowModel(None, app)
        main_window = cls(view, model, password_asker, status_bar, toolbar, navigation)
        model.setParent(main_window)
        return main_window

    @classmethod
    def startup(cls, app):
        """

        :param sakia.app.Application app:
        :return:
        """
        password_asker = PasswordAskerDialog(None)
        navigation = NavigationController.create(None, app)
        toolbar = ToolbarController.create(app, navigation)
        main_window = cls.create(app, password_asker=password_asker,
                                 status_bar=StatusBarController.create(app),
                                 navigation=navigation,
                                 toolbar=toolbar
                                 )
        currencies = app.db.connections_repo.get_currencies()
        if currencies:
            currency = currencies[0]
        else:
            currency = ""

        #app.version_requested.connect(main_window.latest_version_requested)
        #app.account_imported.connect(main_window.import_account_accepted)
        #app.account_changed.connect(main_window.change_account)

        main_window.view.showMaximized()
        main_window.refresh(currency)
        return main_window

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                             error,
                             QMessageBox.Ok)

    @pyqtSlot(int)
    def referential_changed(self, index):
        pass

    @pyqtSlot()
    def latest_version_requested(self):
        latest = self.app.available_version
        logging.debug("Latest version requested")
        if not latest[0]:
            version_info = self.tr("Please get the latest release {version}") \
                .format(version=latest[1])
            version_url = latest[2]

            if self.app.preferences['notifications']:
                toast.display("sakia", """{version_info}""".format(
                version_info=version_info,
                version_url=version_url))

    def refresh(self, currency):
        """
        Refresh main window
        When the selected account changes, all the widgets
        in the window have to be refreshed
        """
        self.status_bar.refresh()
        self.toolbar.enable_actions(len(self.navigation.model.navigation[0]['children']) > 0)
        self.view.setWindowTitle(self.tr("sakia {0} - {currency}").format(__version__, currency=currency))

    def eventFilter(self, target, event):
        """
        Event filter on the widget
        :param QObject target: the target of the event
        :param QEvent event: the event
        :return: bool
        """
        if target == self.widget:
            if event.type() == QEvent.LanguageChange:
                self.ui.retranslateUi(self)
                self.refresh()
            return self.widget.eventFilter(target, event)
        return False

