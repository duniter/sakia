'''
Created on 22 mai 2014

@author: inso
'''
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QErrorMessage, QFileDialog

from cutecoin.models.node import Node
from cutecoin.tools.exceptions import Error
from cutecoin.gen_resources.createWalletDialog_uic import Ui_CreateWalletDialog
from cutecoin.gui.generateWalletKeyDialog import GenerateWalletKeyDialog


class Step():
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        name = self.config_dialog.edit_name.text()
        if name == "":
            return False
        wallets = self.config_dialog.account.wallets
        currency = self.config_dialog.community.currency
        for w in wallets.community_wallets(currency):
            if w.name == name:
                return False
        return True

    def process_next(self):
        self.config_dialog.keyname = self.config_dialog.edit_name.text()

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


class StepPageKey(Step):
    '''
    The step where the user set its key
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    #TODO: Check page validity
    def is_valid(self):
        return self.config_dialog.keyid != ''

    def process_next(self):
        pass

    def display_page(self):
        self.config_dialog.button_next.setEnabled(False)


class StepPageNode(Step):
    '''
    The step where the user set default node
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    #TODO: Check page validity
    def is_valid(self):
        address = self.config_dialog.edit_address.text()
        port = self.config_dialog.spinbox_port.value()
        try:
            peering = Node.create(address, port).peering()
        except ValueError as e:
            self.config_dialog.label_error.setText("Cannot access node : %s" + str(e))
            return False
        except ConnectionError as e:
            self.config_dialog.label_error.setText("Cannot access node : %s" + str(e))
            return False

        if "currency" in peering:
            if (peering['currency'] != self.config_dialog.community.currency):
                self.config_dialog.label_error.setText("This node doesn't use currency %s"
                                         % self.config_dialog.community.currency)
                return False
        else:
            self.config_dialog.label_error.setText("Not a ucoin node")
            return False
        return True

    def process_next(self):
        pass

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


class ProcessCreateWallet(QDialog, Ui_CreateWalletDialog):

    '''
    classdocs
    '''

    def __init__(self, account, community):
        '''
        Constructor
        '''
        super(ProcessCreateWallet, self).__init__()
        self.setupUi(self)
        self.keyid = ''
        self.account = account
        self.community = community
        self.keygen_dialog = None
        self.keyname = ""
        self.step = StepPageInit(self)
        step_key = StepPageKey(self)
        step_node = StepPageNode(self)
        self.step.next_step = step_key
        step_key.next_step = step_node
        self.step.display_page()

    def accept(self):
        address = self.edit_address.text()
        port = self.spinbox_port.value()

        self.account.wallets.add_wallet(self.account.gpg,
                                        self.keyid,
                                        self.community.currency,
                                        Node.create(address, port),
                                        name=self.edit_name.text())
        self.accepted.emit()
        self.close()

    def open_generate_key(self):
        self.keygen_dialog = GenerateWalletKeyDialog(self.account,
                                                     self.keyname)
        self.keygen_dialog.accepted.connect(self.key_generated)
        self.keygen_dialog.exec_()

    def key_generated(self):
        if self.keyid is not '':
            self.account.gpg.delete_keys(self.keyid)

        self.keyid = self.keygen_dialog.keyid
        self.label_fingerprint.setText(self.keygen_dialog.fingerprint)
        self.check()

    def open_import_key(self):
        keyfile = QFileDialog.getOpenFileName(self,
                                              "Choose a secret key",
                                              "",
                                              "All key files (*.asc);; Any file (*)")
        keyfile = keyfile[0]
        key = open(keyfile).read()
        result = self.account.gpg.import_keys(key)
        if result.count == 0:
            QErrorMessage(self).showMessage("Bad key file")
        else:
            QMessageBox.information(self, "Key import", "Key " +
                                    result.fingerprints[0] + " has been imported",
                            QMessageBox.Ok)
            if self.keyid is not '':
                self.account.gpg.delete_keys(self.account.keyid)

            secret_keys = self.account.gpg.list_keys(True)
            for k in secret_keys:
                if k['fingerprint'] == result.fingerprints[0]:
                    self.keyid = k['keyid']

            self.label_fingerprint.setText("Key : " + result.fingerprints[0])
            self.edit_secretkey_path.setText(keyfile)
        self.check()

    def next(self):
        if self.step.next_step is not None:
            if self.step.is_valid():
                self.step.process_next()
                self.step = self.step.next_step
                next_index = self.stacked_pages.currentIndex() + 1
                self.stacked_pages.setCurrentIndex(next_index)
                self.step.display_page()
        else:
            self.accept()

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    def check(self):
        if self.step.is_valid():
            self.button_next.setEnabled(True)
