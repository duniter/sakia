from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from .account_cfg_uic import Ui_AccountConfigurationDialog
from duniterpy.key import SigningKey


class AccountConfigView(QDialog, Ui_AccountConfigurationDialog):
    """
    Home screen view
    """
    values_changed = pyqtSignal()

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)
        self.edit_account_name.textChanged.connect(self.values_changed)
        self.edit_password.textChanged.connect(self.values_changed)
        self.edit_password_repeat.textChanged.connect(self.values_changed)
        self.edit_salt.textChanged.connect(self.values_changed)
        self.button_generate.clicked.connect(self.action_show_pubkey)

    def set_creation_layout(self):
        """
        Hide unecessary buttons and display correct title
        """
        self.setWindowTitle(self.tr("New account"))
        self.button_delete.hide()

    def set_modification_layout(self, account_name):
        """
        Hide unecessary widgets for account modification
        and display correct title
        :return:
        """
        self.label_action.setText("Edit account uid")
        self.edit_account_name.setPlaceholderText(account_name)
        self.button_next.setEnabled(True)
        self.setWindowTitle(self.tr("Configure {0}".format(account_name)))

    def action_show_pubkey(self):
        salt = self.edit_salt.text()
        password = self.edit_password.text()
        pubkey = SigningKey(salt, password).pubkey
        self.label_info.setText(pubkey)

    def account_name(self):
        return self.edit_account_name.text()

    def set_communities_list_model(self, model):
        """
        Set communities list model
        :param sakia.models.communities.CommunitiesListModel model:
        """
        self.list_communities.setModel(model)
