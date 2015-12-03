"""
Created on 24 dec. 2014

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QApplication

from PyQt5.QtCore import Qt

from ..gen_resources.certification_uic import Ui_CertificationDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify
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

        for contact in certifier.contacts:
            self.combo_contact.addItem(contact['name'])

    @classmethod
    @asyncio.coroutine
    def certify_identity(cls, app, account, password_asker, community, identity):
        dialog = cls(app, account, password_asker)
        dialog.combo_community.setCurrentText(community.name)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.radio_pubkey.setChecked(True)
        return (yield from dialog.async_exec())

    @asyncify
    @asyncio.coroutine
    def accept(self):
        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            pubkey = self.account.contacts[index]['pubkey']
        else:
            pubkey = self.edit_pubkey.text()

        password = yield from self.password_asker.async_exec()
        if password == "":
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = yield from self.account.certify(password, self.community, pubkey)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Certification"),
                              self.tr("Success sending certification"))
            else:
                yield from QAsyncMessageBox.information(self, self.tr("Certification"),
                                             self.tr("Success sending certification"))
            QApplication.restoreOverrideCursor()
            super().accept()
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Certification"), self.tr("Could not broadcast certification : {0}"
                                                                .format(result[1])))
            else:
                yield from QAsyncMessageBox.critical(self, self.tr("Certification"),
                                          self.tr("Could not broadcast certification : {0}"
                                                                .format(result[1])))
            QApplication.restoreOverrideCursor()

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        self.refresh()

    @asyncify
    @asyncio.coroutine
    def refresh(self):
        account_identity = yield from self.account.identity(self.community)
        is_member = yield from account_identity.is_member(self.community)
        try:
            block_0 = yield from self.community.get_block(0)
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

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        return future
