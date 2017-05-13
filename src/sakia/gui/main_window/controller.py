import logging

from PyQt5.QtCore import QEvent, pyqtSlot, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QApplication

from sakia.constants import ROOT_SERVERS
from .model import MainWindowModel
from .status_bar.controller import StatusBarController
from .toolbar.controller import ToolbarController
from .view import MainWindowView
from ..navigation.controller import NavigationController
from ..widgets import toast
from ...__init__ import __version__


class MainWindowController(QObject):
    """
    classdocs
    """

    def __init__(self, view, model, status_bar, toolbar, navigation):
        """
        Init
        :param MainWindowView view: the ui of the mainwindow component
        :param sakia.gui.main_window.model.MainWindowModel: the model of the mainwindow component
        :param sakia.gui.main_window.status_bar.controller.StatusBarController status_bar: the controller of the status bar component
        :param sakia.gui.main_window.toolbar.controller.ToolbarController toolbar: the controller of the toolbar component
        :param sakia.gui.navigation.controller.NavigationController navigation: the controller of the navigation

        :param PasswordAsker password_asker: the password asker of the application
        :type: sakia.core.app.Application
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.view = view
        self.model = model
        self.initialized = False
        self.status_bar = status_bar
        self.toolbar = toolbar
        self.navigation = navigation
        self.stacked_widgets = {}
        self.view.bottom_layout.insertWidget(0, self.navigation.view)
        self.view.top_layout.addWidget(self.toolbar.view)
        self.view.setStatusBar(self.status_bar.view)

        QApplication.setWindowIcon(QIcon(":/icons/sakia_logo"))

    @classmethod
    def create(cls, app, status_bar, toolbar, navigation):
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
        main_window = cls(view, model, status_bar, toolbar, navigation)
        model.setParent(main_window)
        return main_window

    @classmethod
    def startup(cls, app):
        """

        :param sakia.app.Application app:
        :return:
        """
        navigation = NavigationController.create(None, app)
        toolbar = ToolbarController.create(app, navigation)
        main_window = cls.create(app, status_bar=StatusBarController.create(app),
                                 navigation=navigation,
                                 toolbar=toolbar
                                 )
        toolbar.view.button_network.clicked.connect(navigation.open_network_view)
        toolbar.view.button_identity.clicked.connect(navigation.open_identities_view)
        toolbar.view.button_explore.clicked.connect(navigation.open_wot_view)
        toolbar.exit_triggered.connect(main_window.view.close)
        #app.version_requested.connect(main_window.latest_version_requested)
        #app.account_imported.connect(main_window.import_account_accepted)
        #app.account_changed.connect(main_window.change_account)
        if app.parameters.maximized:
            main_window.view.showMaximized()
        else:
            main_window.view.show()
        app.refresh_started.connect(main_window.status_bar.start_loading)
        app.refresh_finished.connect(main_window.status_bar.stop_loading)
        main_window.model.load_plugins(main_window)
        main_window.refresh(app.currency)
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
        display_name = ROOT_SERVERS[currency]["display"]
        self.view.setWindowTitle(self.tr("sakia {0} - {1}").format(__version__, display_name))

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

