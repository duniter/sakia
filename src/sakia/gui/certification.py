"""
Created on 24 dec. 2014

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QApplication, QMessageBox

from PyQt5.QtCore import Qt, QObject

from ..gen_resources.certification_uic import Ui_CertificationDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify, once_at_a_time
from ..tools.exceptions import NoPeerAvailable


class CertificationDialog(QObject):
    """
    classdocs
    """

    def __init__(self, app, account, password_asker, widget=QDialog, view=Ui_CertificationDialog):
        """
        Constructor if a certification dialog

        :param sakia.core.Application app:
        :param sakia.core.Account account:
        :param sakia.gui.password_asker.PasswordAsker password_asker:
        :param class widget: the widget of the dialog
        :param class view: the view of the certification dialog
        :return:
        """
        super().__init__()
        self.widget = widget()
        self.ui = view()
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

        self.ui.search_user.button_reset.hide()
        self.ui.search_user.init(self.app)
        self.ui.search_user.change_account(self.account)
        self.ui.search_user.change_community(self.community)
        self.ui.combo_community.currentIndexChanged.connect(self.change_current_community)

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
        dialog.ui.combo_community.setCurrentText(community.name)
        dialog.ui.edit_pubkey.setText(identity.pubkey)
        dialog.ui.radio_pubkey.setChecked(True)
        return await dialog.async_exec()

    @asyncify
    async def accept(self):
        self.ui.button_box.setEnabled(False)
        if self.ui.radio_contact.isChecked():
            for contact in self.account.contacts:
                if contact['name'] == self.ui.combo_contact.currentText():
                    pubkey = contact['pubkey']
                    break
        elif self.ui.radio_search.isChecked():
            if self.ui.search_user.current_identity():
                pubkey = self.ui.search_user.current_identity().pubkey
            else:
                return
        else:
            pubkey = self.ui.edit_pubkey.text()

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
            self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            self.ui.button_box.button(QDialogButtonBox.Ok).setText(self.tr("&Ok"))
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
