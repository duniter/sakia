from PyQt5.QtWidgets import QFrame, QAction, QMenu, QDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QT_TRANSLATE_NOOP, Qt
from .model import ToolbarModel
from .view import ToolbarView
from .toolbar_uic import Ui_SakiaToolbar
from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..widgets.dialogs import QAsyncMessageBox, QAsyncFileDialog, dialog_async_exec
from ..widgets import toast
import logging


class ToolbarController(QObject):
    """
    The navigation panel
    """
    _action_showinfo_text = QT_TRANSLATE_NOOP("CommunityWidget", "Show informations")
    _action_explore_text = QT_TRANSLATE_NOOP("CommunityWidget", "Explore the Web of Trust")
    _action_publish_uid_text = QT_TRANSLATE_NOOP("CommunityWidget", "Publish UID")
    _action_revoke_uid_text = QT_TRANSLATE_NOOP("CommunityWidget", "Revoke UID")

    def __init__(self, view, model, account, community, password_asker):
        """

        :param sakia.gui.toolbar.view.ToolbarView view:
        :param sakia.gui.toolbar.model.ToolbarModel model:
        """
        self.view = view
        self.model = model
        self.account = account
        self.community = community
        self.password_asker = password_asker

        tool_menu = QMenu(self.tr("Tools"), self.toolbutton_menu)
        self.toolbutton_menu.setMenu(tool_menu)

        self.action_publish_uid = QAction(self.tr(ToolbarController._action_publish_uid_text), self)
        self.action_revoke_uid = QAction(self.tr(ToolbarController._action_revoke_uid_text), self)
        self.action_showinfo = QAction(self.tr(ToolbarController._action_showinfo_text), self)
        self.action_explorer = QAction(self.tr(ToolbarController._action_explore_text), self)

        action_showinfo = QAction(self.tr("Show informations"), self.toolbutton_menu)
        action_showinfo.triggered.connect(lambda: self.show_closable_tab(self.tab_informations,
                                                                         QIcon(":/icons/informations_icon"),
                                                                         self.tr("Informations")))
        tool_menu.addAction(action_showinfo)

        action_showexplorer = QAction(self.tr("Show explorer"), self.toolbutton_menu)
        action_showexplorer.triggered.connect(lambda: self.show_closable_tab(self.tab_explorer.widget,
                                                                             QIcon(":/icons/explorer_icon"),
                                                                             self.tr("Explorer")))
        tool_menu.addAction(action_showexplorer)

        menu_advanced = QMenu(self.tr("Advanced"), self.toolbutton_menu)
        action_gen_revokation = QAction(self.tr("Save revokation document"), menu_advanced)
        action_gen_revokation.triggered.connect(self.action_save_revokation)
        menu_advanced.addAction(action_gen_revokation)
        tool_menu.addMenu(menu_advanced)

        self.action_publish_uid.triggered.connect(self.publish_uid)
        tool_menu.addAction(self.action_publish_uid)

        self.button_membership.clicked.connect(self.send_membership_demand)

        self.community_view.button_certification.clicked.connect(self.open_certification_dialog)
        self.community_view.button_send_money.clicked.connect(self.open_transfer_money_dialog)

    @classmethod
    def create(cls, parent):
        """
        Instanciate a navigation agent
        :param sakia.gui.agent.controller.AgentController parent:
        :return: a new Toolbar controller
        :rtype: ToolbarController
        """
        view = ToolbarView(parent.view)
        model = ToolbarModel(None)
        toolbar = cls(view, model)
        model.setParent(toolbar)
        return toolbar

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_block)
        cancel_once_task(self, self.refresh_status)
        logging.debug("Cancelled status")
        cancel_once_task(self, self.refresh_quality_buttons)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()
        self.account = account
        self.password_asker = password_asker

    def change_community(self, community):
        self.cancel_once_tasks()

        logging.debug("Changed community to {0}".format(community))
        self.button_membership.setText(self.tr("Membership"))
        self.button_membership.setEnabled(False)
        self.button_certification.setEnabled(False)
        self.action_publish_uid.setEnabled(False)
        self.community = community
        self.refresh_quality_buttons()

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

    @once_at_a_time
    @asyncify
    async def refresh_quality_buttons(self):
        if self.account and self.community:
            try:
                account_identity = await self.account.identity(self.community)
                published_uid = await account_identity.published_uid(self.community)
                uid_is_revokable = await account_identity.uid_is_revokable(self.community)
                if published_uid:
                    logging.debug("UID Published")
                    self.action_revoke_uid.setEnabled(uid_is_revokable)
                    is_member = await account_identity.is_member(self.community)
                    if is_member:
                        self.button_membership.setText(self.tr("Renew membership"))
                        self.button_membership.setEnabled(True)
                        self.button_certification.setEnabled(True)
                        self.action_publish_uid.setEnabled(False)
                    else:
                        logging.debug("Not a member")
                        self.button_membership.setText(self.tr("Send membership demand"))
                        self.button_membership.setEnabled(True)
                        self.action_publish_uid.setEnabled(False)
                        if await self.community.get_block(0) is not None:
                            self.button_certification.setEnabled(False)
                else:
                    logging.debug("UID not published")
                    self.button_membership.setEnabled(False)
                    self.button_certification.setEnabled(False)
                    self.action_publish_uid.setEnabled(True)
            except LookupFailureError:
                self.button_membership.setEnabled(False)
                self.button_certification.setEnabled(False)
                self.action_publish_uid.setEnabled(False)

    def open_certification_dialog(self):
        CertificationDialog.open_dialog(self.app,
                                     self.account,
                                     self.community_view.community,
                                     self.password_asker)

    def open_revocation_dialog(self):
        RevocationDialog.open_dialog(self.app,
                                     self.account)

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app,
                                     self.account,
                                     self.password_asker,
                                     self.community_view.community,
                                     None)
        if dialog.exec() == QDialog.Accepted:
            self.community_view.tab_history.table_history.model().sourceModel().refresh_transfers()

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
