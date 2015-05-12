'''
Created on 24 dec. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QApplication
from PyQt5.QtCore import Qt
from ..tools.exceptions import NoPeerAvailable
from ..gen_resources.certification_uic import Ui_CertificationDialog
from . import toast


class CertificationDialog(QDialog, Ui_CertificationDialog):

    '''
    classdocs
    '''

    def __init__(self, certifier, password_asker):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
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

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.account.certify(password, self.community, pubkey)
            toast.display(self.tr("Certification"),
                          self.tr("Success certifying {0} from {1}").format(pubkey,
                                                                          self.community.currency))
        except ValueError as e:
            QMessageBox.critical(self, self.tr("Certification"),
                                 self.tr("Something wrong happened : {0}").format(e),
                                 QMessageBox.Ok)
            return
        except NoPeerAvailable as e:
            QMessageBox.critical(self, self.tr("Certification"),
                                 self.tr("Couldn't connect to network : {0}").format(e),
                                 QMessageBox.Ok)
            return
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 "{0}".format(e),
                                 QMessageBox.Ok)
            return
        finally:
            QApplication.restoreOverrideCursor()

        super().accept()

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
