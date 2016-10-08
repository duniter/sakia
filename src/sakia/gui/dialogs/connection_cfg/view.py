from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from .connection_cfg_uic import Ui_ConnectionConfigurationDialog
from duniterpy.key import SigningKey
from ...widgets import toast
from ...widgets.dialogs import QAsyncMessageBox


class ConnectionConfigView(QDialog, Ui_ConnectionConfigurationDialog):
    """
    Connection config view
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

    def display_info(self, info):
        self.label_info.setText(info)

    def set_currency(self, currency):
        self.label_currency.setText(currency)

    def add_node_parameters(self):
        server = self.lineedit_add_address.text()
        port = self.spinbox_add_port.value()
        return server, port

    async def show_success(self, notification):
        if notification:
            toast.display(self.tr("UID broadcast"), self.tr("Identity broadcasted to the network"))
        else:
            await QAsyncMessageBox.information(self, self.tr("UID broadcast"),
                                               self.tr("Identity broadcasted to the network"))

    def show_error(self, notification, error_txt):
        if notification:
            toast.display(self.tr("UID broadcast"), error_txt)
        self.label_info.setText(self.tr("Error") + " " + error_txt)

    def set_nodes_model(self, model):
        self.tree_peers.setModel(model)


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

    def stream_log(self, log):
        """
        Add log to
        :param str log:
        """
        self.plain_text_edit.insertPlainText("\n" + log)
