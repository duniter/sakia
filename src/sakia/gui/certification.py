"""
Created on 24 dec. 2014

@author: inso
"""
import asyncio
import logging
from ucoinpy.api import errors
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QObject, QLocale, QDateTime

from .widgets import toast
from .widgets.dialogs import QAsyncMessageBox
from .member import MemberDialog
from ..tools.decorators import asyncify, once_at_a_time
from ..tools.exceptions import NoPeerAvailable
from ..gen_resources.certification_uic import Ui_CertificationDialog

class CertificationDialog(QObject):
    """
    A dialog to certify individuals
    """

    def __init__(self, app, account, password_asker, widget, ui):
        """
        Constructor if a certification dialog

        :param sakia.core.Application app:
        :param sakia.core.Account account:
        :param sakia.gui.password_asker.PasswordAsker password_asker:
        :param PyQt5.QtWidgets widget: the widget of the dialog
        :param sakia.gen_resources.certification_uic.Ui_CertificationDialog view: the view of the certification dialog
        :return:
        """
        super().__init__()
        self.widget = widget
        self.ui = ui
        self.ui.setupUi(self.widget)
        self.app = app
        self.account = account
        self.password_asker = password_asker
        self.community = self.account.communities[0]

        self.ui.radio_contact.toggled.connect(lambda c, radio="contact": self.recipient_mode_changed(radio))
        self.ui.radio_pubkey.toggled.connect(lambda c, radio="pubkey": self.recipient_mode_changed(radio))
        self.ui.radio_search.toggled.connect(lambda c, radio="search": self.recipient_mode_changed(radio))
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.widget.reject)

        for community in self.account.communities:
            self.ui.combo_community.addItem(community.currency)

        for contact_name in sorted([c['name'] for c in account.contacts], key=str.lower):
            self.ui.combo_contact.addItem(contact_name)

        if len(account.contacts) == 0:
            self.ui.radio_pubkey.setChecked(True)
            self.ui.radio_contact.setEnabled(False)

        self.ui.member_widget = MemberDialog.as_widget(self.ui.groupBox, self.app, self.account, self.community, None)
        self.ui.horizontalLayout_5.addWidget(self.ui.member_widget.widget)

        self.ui.search_user.button_reset.hide()
        self.ui.search_user.init(self.app)
        self.ui.search_user.change_account(self.account)
        self.ui.search_user.change_community(self.community)
        self.ui.combo_contact.currentIndexChanged.connect(self.refresh_member)
        self.ui.edit_pubkey.textChanged.connect(self.refresh_member)
        self.ui.search_user.identity_selected.connect(self.refresh_member)
        self.ui.radio_contact.toggled.connect(self.refresh_member)
        self.ui.radio_search.toggled.connect(self.refresh_member)
        self.ui.radio_pubkey.toggled.connect(self.refresh_member)
        self.ui.combo_community.currentIndexChanged.connect(self.change_current_community)

    @classmethod
    def open_dialog(cls, app, account, community, password_asker):
        """
        Certify and identity
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.core.Community community: the community
        :param sakia.gui.password_asker.PasswordAsker password_asker: the password asker
        :return:
        """
        dialog = cls(app, account, password_asker, QDialog(), Ui_CertificationDialog())
        dialog.ui.combo_community.setCurrentText(community.name)
        dialog.refresh()
        return dialog.exec()

    @classmethod
    async def certify_identity(cls, app, account, password_asker, community, identity):
        """
        Certify and identity
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.gui.password_asker.PasswordAsker password_asker: the password asker
        :param sakia.core.Community community: the community
        :param sakia.core.registry.Identity identity: the identity certified
        :return:
        """
        dialog = cls(app, account, password_asker, QDialog(), Ui_CertificationDialog())
        dialog.ui.combo_community.setCurrentText(community.name)
        dialog.ui.edit_pubkey.setText(identity.pubkey)
        dialog.ui.radio_pubkey.setChecked(True)
        dialog.refresh()
        return await dialog.async_exec()

    @asyncify
    async def accept(self):
        """
        Validate the dialog
        """
        pubkey = self.selected_pubkey()
        if pubkey:
            password = await self.password_asker.async_exec()
            if password == "":
                self.ui.button_box.setEnabled(True)
                return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            result = await self.account.certify(password, self.community, pubkey)
            if result[0]:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Certification"),
                                  self.tr("Success sending certification"))
                else:
                    await QAsyncMessageBox.information(self.widget, self.tr("Certification"),
                                                 self.tr("Success sending certification"))
                QApplication.restoreOverrideCursor()
                self.widget.accept()
            else:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Certification"), self.tr("Could not broadcast certification : {0}"
                                                                    .format(result[1])))
                else:
                    await QAsyncMessageBox.critical(self.widget, self.tr("Certification"),
                                              self.tr("Could not broadcast certification : {0}"
                                                                    .format(result[1])))
                QApplication.restoreOverrideCursor()
                self.ui.button_box.setEnabled(True)

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        self.ui.search_user.change_community(self.community)
        self.ui.member_widget.change_community(self.community)
        if self.widget.isVisible():
            self.refresh()

    def selected_pubkey(self):
        """
        Get selected pubkey in the widgets of the window
        :return: the current pubkey
        :rtype: str
        """
        pubkey = None
        if self.ui.radio_contact.isChecked():
            for contact in self.account.contacts:
                if contact['name'] == self.ui.combo_contact.currentText():
                    pubkey = contact['pubkey']
                    break
        elif self.ui.radio_search.isChecked():
            if self.ui.search_user.current_identity():
                pubkey = self.ui.search_user.current_identity().pubkey
        else:
            pubkey = self.ui.edit_pubkey.text()
        return pubkey

    @asyncify
    async def refresh_member(self, checked=False):
        """
        Refresh the member widget
        """
        current_pubkey = self.selected_pubkey()
        if current_pubkey:
            identity = await self.app.identities_registry.future_find(current_pubkey, self.community)
        else:
            identity = None
        self.ui.member_widget.identity = identity
        self.ui.member_widget.refresh()

    @once_at_a_time
    @asyncify
    async def refresh(self):
        account_identity = await self.account.identity(self.community)
        is_member = await account_identity.is_member(self.community)
        try:
            block_0 = await self.community.get_block(0)
        except errors.UcoinError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                block_0 = None
        except NoPeerAvailable as e:
            logging.debug(str(e))
            block_0 = None

        params = await self.community.parameters()
        nb_certifications = len(await account_identity.certified_by(self.app.identities_registry, self.community))
        remaining_time = await account_identity.cert_issuance_delay(self.app.identities_registry, self.community)
        cert_text = self.tr("Certifications sent : {nb_certifications}/{stock}").format(
            nb_certifications=nb_certifications,
            stock=params['sigStock'])
        if remaining_time > 0:
            cert_text += self.tr("Remaining time before next available certification : {0}").format(
                QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(remaining_time),
                            QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                        ),
                )
        self.ui.label_cert_stock.setText(cert_text)

        if is_member or not block_0:
            if remaining_time == 0 and (nb_certifications < params['sigStock'] or params['sigStock'] == 0):
                self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                self.ui.button_box.button(QDialogButtonBox.Ok).setText(self.tr("&Ok"))
            else:
                self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                self.ui.button_box.button(QDialogButtonBox.Ok).setText(self.tr("No more certifications"))
        else:
            self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.ui.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Not a member"))

    def showEvent(self, event):
        super().showEvent(event)
        self.first_certification_check()

    def first_certification_check(self):
        if self.account.notifications['warning_certifying_first_time']:
            self.account.notifications['warning_certifying_first_time'] = False
            QMessageBox.warning(self, "Certifying individuals", """Please follow the following guidelines :
1.) Don't certify an account if you believe the issuers identity might be faked.
2.) Don't certify an account if you believe the issuer already has another certified account.
3.) Don't certify an account if you believe the issuer purposely or carelessly violates rule 1 or 2 (the issuer certifies faked or double accounts
""")

    def recipient_mode_changed(self, radio):
        """
        :param str radio:
        """
        self.ui.edit_pubkey.setEnabled(radio == "pubkey")
        self.ui.combo_contact.setEnabled(radio == "contact")
        self.ui.search_user.setEnabled(radio == "search")

    def async_exec(self):
        future = asyncio.Future()
        self.widget.finished.connect(lambda r: future.set_result(r))
        self.widget.open()
        self.refresh()
        return future

    def exec(self):
        self.widget.exec()
