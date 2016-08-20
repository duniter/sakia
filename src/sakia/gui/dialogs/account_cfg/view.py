from PyQt5.QtWidgets import QWidget
from .account_cfg_uic import Ui_AccountConfigurationDialog


class AccountConfigView(QWidget, Ui_AccountConfigurationDialog):
    """
    Home screen view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)

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

    def account_name(self):
        return self.edit_account_name.text()
