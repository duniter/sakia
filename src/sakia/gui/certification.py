"""
Created on 24 dec. 2014

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QApplication, QMessageBox

from PyQt5.QtCore import Qt

from ..gen_resources.certification_uic import Ui_CertificationDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify, once_at_a_time
from ..tools.exceptions import NoPeerAvailable


class CertificationDialog(QDialog, Ui_CertificationDialog):
    """
    classdocs
    """

    def __init__(self, app, certifier, password_asker):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = certifier
        self.password_asker = password_asker
        self.community = self.account.communities[0]

        for community in self.account.communities:
            self.combo_community.addItem(community.currency)

        for contact_name in sorted([c['name'] for c in certifier.contacts], key=str.lower):
            self.combo_contact.addItem(contact_name)

        if len(certifier.contacts) == 0:
            self.radio_pubkey.setChecked(True)
            self.radio_contact.setEnabled(False)

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
        dialog = cls(app, account, password_asker)
        dialog.combo_community.setCurrentText(community.name)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.radio_pubkey.setChecked(True)
        return await dialog.async_exec()

    @asyncify
    async def accept(self):
        self.button_box.setEnabled(False)
        if self.radio_contact.isChecked():
            for contact in self.account.contacts:
                if contact['name'] == self.combo_contact.currentText():
                    pubkey = contact['pubkey']
                    break
        else:
            pubkey = self.edit_pubkey.text()

        password = await self.password_asker.async_exec()
        if password == "":
            self.button_box.setEnabled(True)
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = await self.account.certify(password, self.community, pubkey)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Certification"),
                              self.tr("Success sending certification"))
            else:
                await QAsyncMessageBox.information(self, self.tr("Certification"),
                                             self.tr("Success sending certification"))
            QApplication.restoreOverrideCursor()
            super().accept()
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Certification"), self.tr("Could not broadcast certification : {0}"
                                                                .format(result[1])))
            else:
                await QAsyncMessageBox.critical(self, self.tr("Certification"),
                                          self.tr("Could not broadcast certification : {0}"
                                                                .format(result[1])))
            QApplication.restoreOverrideCursor()
            self.button_box.setEnabled(True)

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        if self.isVisible():
            self.refresh()

    @once_at_a_time
    @asyncify
    async def refresh(self):
        account_identity = await self.account.identity(self.community)
        is_member = await account_identity.is_member(self.community)
        try:
            block_0 = await self.community.get_block(0)
        except ValueError as e:
            if '404' in str(e) or '000' in str(e):
                block_0 = None
        except NoPeerAvailable as e:
            logging.debug(str(e))
            block_0 = None

        if is_member or not block_0:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("&Ok"))
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Not a member"))

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

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        self.refresh()
        return future
