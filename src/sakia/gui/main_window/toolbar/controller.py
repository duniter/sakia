import logging

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QDialog, QMessageBox

from sakia.decorators import asyncify
from sakia.gui.dialogs.connection_cfg.controller import ConnectionConfigController
from sakia.gui.dialogs.certification.controller import CertificationController
from sakia.gui.dialogs.transfer.controller import TransferController
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox, QAsyncFileDialog, dialog_async_exec
from .model import ToolbarModel
from .view import ToolbarView


class ToolbarController(QObject):
    """
    The navigation panel
    """

    def __init__(self, view, model):
        """
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.gui.toolbar.view.ToolbarView view:
        :param sakia.gui.toolbar.model.ToolbarModel model:
        """
        super().__init__()
        self.view = view
        self.model = model
        self.view.button_certification.clicked.connect(self.open_certification_dialog)
        self.view.button_send_money.clicked.connect(self.open_transfer_money_dialog)
        self.view.action_gen_revokation.triggered.connect(self.action_save_revokation)
        self.view.action_publish_uid.triggered.connect(self.publish_uid)
        self.view.button_membership.clicked.connect(self.send_membership_demand)
        self.view.action_create_account.triggered.connect(self.open_create_account_dialog)

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

    @asyncify
    async def action_save_revokation(self, checked=False):
        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return

        raw_document = await self.account.generate_revokation(self.community, password)
        # Testable way of using a QFileDialog
        selected_files = await QAsyncFileDialog.get_save_filename(self, self.tr("Save a revokation document"),
                                                                  "", self.tr("All text files (*.txt)"))
        if selected_files:
            path = selected_files[0]
            if not path.endswith('.txt'):
                path = "{0}.txt".format(path)
            with open(path, 'w') as save_file:
                save_file.write(raw_document)

        dialog = QMessageBox(QMessageBox.Information, self.tr("Revokation file"),
                             self.tr("""<div>Your revokation document has been saved.</div>
<div><b>Please keep it in a safe place.</b></div>
The publication of this document will remove your identity from the network.</p>"""), QMessageBox.Ok,
                             self)
        dialog.setTextFormat(Qt.RichText)
        await dialog_async_exec(dialog)

    @asyncify
    async def send_membership_demand(self, checked=False):
        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return
        result = await self.account.send_membership(password, self.community, 'IN')
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
            else:
                await QAsyncMessageBox.information(self, self.tr("Membership"),
                                                        self.tr("Success sending Membership demand"))
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Membership"), result[1])
            else:
                await QAsyncMessageBox.critical(self, self.tr("Membership"),
                                                        result[1])

    @asyncify
    async def send_membership_leaving(self):
        reply = await QAsyncMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return
            result = await self.account.send_membership(password, self.community, 'OUT')
            if result[0]:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), self.tr("Success sending Revoke demand"))
                else:
                    await QAsyncMessageBox.information(self, self.tr("Revoke"),
                                                            self.tr("Success sending Revoke demand"))
            else:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), result[1])
                else:
                    await QAsyncMessageBox.critical(self, self.tr("Revoke"),
                                                         result[1])

    @asyncify
    async def publish_uid(self, checked=False):
        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return
        result = await self.account.send_selfcert(password, self.community)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("UID"), self.tr("Success publishing your UID"))
            else:
                await QAsyncMessageBox.information(self, self.tr("Membership"),
                                                        self.tr("Success publishing your UID"))
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("UID"), result[1])
            else:
                await QAsyncMessageBox.critical(self, self.tr("UID"),
                                                        result[1])

    def set_account(self, account):
        """
        Set current account
        :param sakia.core.Account account:
        """
        self.model.account = account

    def set_community(self, community):
        """
        Set current community
        :param sakia.core.Community community:
        """
        self.model.community = community

    def open_certification_dialog(self):
        CertificationController.open_dialog(self, self.model.app,
                                            self.model.navigation_model.current_connection())

    def open_revocation_dialog(self):
        RevocationDialog.open_dialog(self.app,
                                     self.account)

    def open_transfer_money_dialog(self):
        TransferController.open_dialog(self, self.model.app,
                                       account=self.model.account,
                                       password_asker=self.password_asker)

    def open_create_account_dialog(self):
        ConnectionConfigController.create_connection(self, self.model.app).exec()
        self.model.app.instanciate_services()
        self.model.app.start_coroutines()

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
