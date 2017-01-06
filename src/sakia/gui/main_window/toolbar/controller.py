from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QDialog, QMessageBox

from sakia.decorators import asyncify
from sakia.gui.dialogs.connection_cfg.controller import ConnectionConfigController
from sakia.gui.dialogs.certification.controller import CertificationController
from sakia.gui.dialogs.revocation.controller import RevocationController
from sakia.gui.dialogs.transfer.controller import TransferController
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox, QAsyncFileDialog, dialog_async_exec
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.gui.preferences import PreferencesDialog
from .model import ToolbarModel
from .view import ToolbarView


class ToolbarController(QObject):
    """
    The navigation panel
    """

    def __init__(self, view, model):
        """
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.gui.main_window.toolbar.view.ToolbarView view:
        :param sakia.gui.main_window.toolbar.model.ToolbarModel model:
        """
        super().__init__()
        self.view = view
        self.model = model
        self.view.button_certification.clicked.connect(self.open_certification_dialog)
        self.view.button_send_money.clicked.connect(self.open_transfer_money_dialog)
        self.view.button_membership.clicked.connect(self.send_join_demand)
        self.view.action_add_connection.triggered.connect(self.open_add_connection_dialog)
        self.view.action_parameters.triggered.connect(self.open_settings_dialog)

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
        model = ToolbarModel(app, navigation.model)
        toolbar = cls(view, model)
        return toolbar

    def enable_actions(self, enabled):
        self.view.button_certification.setEnabled(enabled)
        self.view.button_send_money.setEnabled(enabled)
        self.view.button_membership.setEnabled(enabled)

    @asyncify
    async def send_join_demand(self, checked=False):
        connection = await self.view.ask_for_connection(self.model.connections())
        if not connection:
            return
        password = await PasswordAskerDialog(connection).async_exec()
        if not password:
            return
        result = await self.model.send_join(connection, password)
        if result[0]:
            if self.model.notifications():
                toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
            else:
                await QAsyncMessageBox.information(self, self.tr("Membership"),
                                                        self.tr("Success sending Membership demand"))
        else:
            if self.model.notifications():
                toast.display(self.tr("Membership"), result[1])
            else:
                await QAsyncMessageBox.critical(self, self.tr("Membership"),
                                                        result[1])

    def open_certification_dialog(self):
        CertificationController.open_dialog(self, self.model.app,
                                            self.model.navigation_model.current_connection())

    def open_revocation_dialog(self):
        RevocationController.open_dialog(self.app, self.model.navigation_model.current_connection())

    def open_transfer_money_dialog(self):
        TransferController.open_dialog(self, self.model.app, self.model.navigation_model.current_connection())

    def open_settings_dialog(self):
        PreferencesDialog(self.model.app).exec()

    def open_add_connection_dialog(self):
        connection_config = ConnectionConfigController.create_connection(self, self.model.app)
        connection_config.exec()
        if connection_config.view.result() == QDialog.Accepted:
            self.model.app.instanciate_services()
            self.model.app.start_coroutines()
            self.model.app.new_connection.emit(connection_config.model.connection)
            self.enable_actions(True)

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
