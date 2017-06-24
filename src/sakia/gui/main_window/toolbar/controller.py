from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QDialog
from sakia.gui.dialogs.connection_cfg.controller import ConnectionConfigController
from sakia.gui.dialogs.revocation.controller import RevocationController
from sakia.gui.dialogs.contact.controller import ContactController
from sakia.gui.dialogs.plugins_manager.controller import PluginsManagerController
from sakia.gui.preferences import PreferencesDialog
from .model import ToolbarModel
from .view import ToolbarView
from sakia.data.processors import BlockchainProcessor
import sys


class ToolbarController(QObject):
    """
    The navigation panel
    """

    exit_triggered = pyqtSignal()

    def __init__(self, view, model):
        """
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.gui.main_window.toolbar.view.ToolbarView view:
        :param sakia.gui.main_window.toolbar.model.ToolbarModel model:
        """
        super().__init__()
        self.view = view
        self.model = model
        self.view.action_add_connection.triggered.connect(self.open_add_connection_dialog)
        self.view.action_parameters.triggered.connect(self.open_settings_dialog)
        self.view.action_plugins.triggered.connect(self.open_plugins_manager_dialog)
        self.view.action_about.triggered.connect(self.open_about_dialog)
        self.view.action_about_wot.triggered.connect(self.open_about_wot_dialog)
        self.view.action_about_money.triggered.connect(self.open_about_money_dialog)
        self.view.action_about_referentials.triggered.connect(self.open_about_referentials_dialog)
        self.view.action_revoke_uid.triggered.connect(self.open_revocation_dialog)
        self.view.button_contacts.clicked.connect(self.open_contacts_dialog)
        self.view.action_exit.triggered.connect(self.exit_triggered)

    @classmethod
    def create(cls, app, navigation):
        """
        Instanciate a navigation component
        :param sakia.app.Application app:
        :param sakia.gui.navigation.controller.NavigationController navigation:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = ToolbarView(None)
        model = ToolbarModel(app, navigation.model, app.blockchain_service, BlockchainProcessor.instanciate(app))
        toolbar = cls(view, model)
        return toolbar

    def open_contacts_dialog(self):
        ContactController.open_dialog(self, self.model.app)

    def open_revocation_dialog(self):
        RevocationController.open_dialog(self, self.model.app, self.model.navigation_model.current_connection())

    def open_settings_dialog(self):
        PreferencesDialog(self.model.app).exec()

    def open_plugins_manager_dialog(self):
        PluginsManagerController.open_dialog(self, self.model.app)

    def open_add_connection_dialog(self):
        connection_config = ConnectionConfigController.create_connection(self, self.model.app)
        connection_config.exec()
        if connection_config.view.result() == QDialog.Accepted:
            self.model.app.instanciate_services()
            self.model.app.start_coroutines()
            self.model.app.new_connection.emit(connection_config.model.connection)

    def open_about_dialog(self):
        text = self.model.about_text()
        self.view.show_about(text)

    def open_about_wot_dialog(self):
        params = self.model.parameters()
        self.view.show_about_wot(params)

    def open_about_money_dialog(self):
        params = self.model.parameters()
        currency = self.model.app.currency
        localized_data = self.model.get_localized_data()
        referentials = self.model.referentials()
        self.view.show_about_money(params, currency, localized_data)

    def open_about_referentials_dialog(self):
        referentials = self.model.referentials()
        self.view.show_about_referentials(referentials)

    def retranslateUi(self, widget):
        """
        Method to complete translations missing from generated code
        :param widget:
        :return:
        """
        self.action_publish_uid.setText(self.tr(ToolbarController.action_publish_uid_text))
        self.action_revoke_uid.setText(self.tr(ToolbarController.action_revoke_uid_text))
        self.action_showinfo.setText(self.tr(ToolbarController.action_showinfo_text))
        super().retranslateUi(self)
