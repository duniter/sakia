"""
Created on 24 dec. 2014

@author: inso
"""
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QApplication
from PyQt5.QtCore import Qt, pyqtSlot
import quamash
from ..gen_resources.certification_uic import Ui_CertificationDialog
from . import toast
import asyncio


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

    def accept(self):
        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            pubkey = self.account.contacts[index]['pubkey']
        else:
            pubkey = self.edit_pubkey.text()

        password = self.password_asker.exec_()
        if password == "":
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.account.certification_broadcasted.connect(lambda: self.certification_sent(pubkey,
                                                                                       self.community.currency))
        self.account.broadcast_error.connect(self.handle_error)

        asyncio.async(self.account.certify(password, self.community, pubkey))

    def certification_sent(self, pubkey, currency):
        toast.display(self.tr("Certification"),
                      self.tr("Success certifying {0} from {1}").format(pubkey, currency))
        self.account.certification_broadcasted.disconnect()
        self.account.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()
        super().accept()

    @pyqtSlot(int, str)
    def handle_error(self, error_code, text):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Error"), self.tr("{0} : {1}".format(error_code, text)))
        else:
            QMessageBox.Critical(self, self.tr("Error", self.tr("{0} : {1}".format(error_code, text))))
        self.account.certification_broadcasted.disconnect()
        self.account.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        if self.account.pubkey in self.community.members_pubkeys():
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Ok"))
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Not a member"))

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)
