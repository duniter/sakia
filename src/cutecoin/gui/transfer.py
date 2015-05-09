'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication
from PyQt5.QtCore import QRegExp, Qt, QLocale
from PyQt5.QtGui import QRegExpValidator

from ..tools.exceptions import NotEnoughMoneyError, NoPeerAvailable
from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog
from . import toast


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    '''
    classdocs
    '''

    def __init__(self, sender, password_asker):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = sender
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.wallet = None
        self.community = self.account.communities[0]
        self.wallet = self.account.wallets[0]
        self.dividend = self.community.dividend

        regexp = QRegExp('^([ a-zA-Z0-9-_:/;*?\[\]\(\)\\\?!^+=@&~#{}|<>%.]{0,255})$')
        validator = QRegExpValidator(regexp)
        self.edit_message.setValidator(validator)

        for community in self.account.communities:
            self.combo_community.addItem(community.currency)

        for wallet in self.account.wallets:
            self.combo_wallets.addItem(wallet.name)

        for contact in sender.contacts:
            self.combo_contact.addItem(contact['name'])

        if len(self.account.contacts) == 0:
            self.combo_contact.setEnabled(False)
            self.radio_contact.setEnabled(False)
            self.radio_pubkey.setChecked(True)

    def accept(self):
        comment = self.edit_message.text()

        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            recipient = self.account.contacts[index]['pubkey']
        else:
            recipient = self.edit_pubkey.text()
        amount = self.spinbox_amount.value()

        if not amount:
            QMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            return

        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            self.wallet.send_money(self.account.salt, password, self.community,
                                       recipient, amount, comment)
            toast.display(self.tr("Money transfer"),
                          self.tr("Success transfering {0} {1} to {2}").format(amount,
                                                                             self.community.currency,
                                                                             recipient))
        except ValueError as e:
            QMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("Something wrong happened : {0}").format(e),
                                 QMessageBox.Ok)
            return
        except NotEnoughMoneyError as e:
            QMessageBox.warning(self, self.tr("Money transfer"),
                                 self.tr("""This transaction could not be sent on this block
Please try again later"""))
        except NoPeerAvailable as e:
            QMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("Couldn't connect to network : {0}").format(e),
                                 QMessageBox.Ok)
            return
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 "{0}".format(str(e)),
                                 QMessageBox.Ok)
            return
        finally:
            QApplication.restoreOverrideCursor()
            QApplication.processEvents()

        super().accept()

    def amount_changed(self):
        amount = self.spinbox_amount.value()
        relative = amount / self.dividend
        self.spinbox_relative.blockSignals(True)
        self.spinbox_relative.setValue(relative)
        self.spinbox_relative.blockSignals(False)

    def relative_amount_changed(self):
        relative = self.spinbox_relative.value()
        amount = relative * self.dividend
        self.spinbox_amount.blockSignals(True)
        self.spinbox_amount.setValue(amount)
        self.spinbox_amount.blockSignals(False)

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        self.dividend = self.community.dividend
        amount = self.wallet.value(self.community)
        ref_amount = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.currency)
        if isinstance(ref_amount, int):
            ref_amount = QLocale().toString(ref_amount)
        else:
            ref_amount = QLocale().toString(ref_amount, 'f', 6)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = self.wallet.value(self.community)
        ref_amount = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.currency)
        if isinstance(ref_amount, int):
            ref_amount = QLocale().toString(ref_amount)
        else:
            ref_amount = QLocale().toString(ref_amount, 'f', 6)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)
