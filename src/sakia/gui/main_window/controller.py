"""
Created on 1 févr. 2014

@author: inso
"""
import aiohttp
import logging
import traceback

from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QEvent, pyqtSlot, QObject
from PyQt5.QtGui import QIcon

from ..password_asker import PasswordAskerDialog
from ...__init__ import __version__
from ..widgets import toast
from ..component.controller import ComponentController
from .view import MainWindowView
from .model import MainWindowModel
from ..status_bar.controller import StatusBarController
from ..toolbar.controller import ToolbarController
from ..navigation.controller import NavigationController
from ..txhistory.controller import TxHistoryController


class MainWindowController(ComponentController):
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
        super().__init__(None, view, model)
        self.initialized = False
        self.password_asker = password_asker
        self.status_bar = self.attach(status_bar)
        self.toolbar = self.attach(toolbar)
        self.navigation = self.attach(navigation)
        self.stacked_widgets = {}

        QApplication.setWindowIcon(QIcon(":/icons/sakia_logo"))

    @classmethod
    def startup(cls, app):
        view = MainWindowView(None)
        model = MainWindowModel(None, app)
        password_asker = PasswordAskerDialog(None)
        main_window = cls(view, model, password_asker, None, None, None)

        main_window.status_bar = main_window.attach(StatusBarController.create(main_window, app))
        view.setStatusBar(main_window.status_bar.view)

        main_window.toolbar = main_window.attach(ToolbarController.create(main_window, password_asker))
        view.top_layout.addWidget(main_window.toolbar.view)

        main_window.navigation = main_window.attach(NavigationController.create(main_window, app))
        view.bottom_layout.insertWidget(0, main_window.navigation.view)

        #app.version_requested.connect(main_window.latest_version_requested)
        #app.account_imported.connect(main_window.import_account_accepted)
        #app.account_changed.connect(main_window.change_account)

        view.showMaximized()
        main_window.refresh()
        return main_window

    def add_to_stack(self, index, widget):
        """
        Add a view to the stack
        :param int index: the index of the page
        :param PyQt5.QtWidgets.QWidget widget: the view
        """
        self.stack.addWidget(widget)
        self.stacked_widgets[index] = widget

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

    def refresh(self):
        """
        Refresh main window
        When the selected account changes, all the widgets
        in the window have to be refreshed
        """
        self.status_bar.refresh()
        self.view.setWindowTitle(self.tr("sakia {0}").format(__version__))

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

