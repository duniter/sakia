from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal, Qt
from .connection_cfg_uic import Ui_ConnectionConfigurationDialog
from duniterpy.key import SigningKey, ScryptParams
from math import ceil, log
from sakia.gui.widgets import toast
from sakia.helpers import timestamp_to_dhms
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from sakia.constants import ROOT_SERVERS


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
        self.edit_uid.textChanged.connect(self.values_changed)
        self.edit_password.textChanged.connect(self.values_changed)
        self.edit_password_repeat.textChanged.connect(self.values_changed)
        self.edit_salt.textChanged.connect(self.values_changed)
        self.edit_pubkey.textChanged.connect(self.values_changed)
        self.button_generate.clicked.connect(self.action_show_pubkey)

        self.combo_scrypt_params.currentIndexChanged.connect(self.handle_combo_change)
        self.scrypt_params = ScryptParams(4096, 16, 1)
        self.spin_n.setMaximum(2 ** 20)
        self.spin_n.setValue(self.scrypt_params.N)
        self.spin_n.valueChanged.connect(self.handle_n_change)
        self.spin_r.setMaximum(128)
        self.spin_r.setValue(self.scrypt_params.r)
        self.spin_r.valueChanged.connect(self.handle_r_change)
        self.spin_p.setMaximum(128)
        self.spin_p.setValue(self.scrypt_params.p)
        self.spin_p.valueChanged.connect(self.handle_p_change)
        self.label_info.setTextFormat(Qt.RichText)

    def handle_combo_change(self, index):
        strengths = [
            (2 ** 12, 16, 1),
            (2 ** 14, 32, 2),
            (2 ** 16, 32, 4),
            (2 ** 18, 64, 8),
        ]
        self.spin_n.blockSignals(True)
        self.spin_r.blockSignals(True)
        self.spin_p.blockSignals(True)
        self.spin_n.setValue(strengths[index][0])
        self.spin_r.setValue(strengths[index][1])
        self.spin_p.setValue(strengths[index][2])
        self.spin_n.blockSignals(False)
        self.spin_r.blockSignals(False)
        self.spin_p.blockSignals(False)

    def handle_n_change(self, value):
        spinbox = self.sender()
        self.scrypt_params.N = ConnectionConfigView.compute_power_of_2(spinbox, value, self.scrypt_params.N)

    def handle_r_change(self, value):
        spinbox = self.sender()
        self.scrypt_params.r = ConnectionConfigView.compute_power_of_2(spinbox, value, self.scrypt_params.r)

    def handle_p_change(self, value):
        spinbox = self.sender()
        self.scrypt_params.p = ConnectionConfigView.compute_power_of_2(spinbox, value, self.scrypt_params.p)

    @staticmethod
    def compute_power_of_2(spinbox, value, param):
        if value > 1:
            if value > param:
                value = pow(2, ceil(log(value) / log(2)))
            else:
                value -= 1
                value = 2 ** int(log(value, 2))
        else:
            value = 1

        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)

        return value

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

    def set_creation_layout(self, currency):
        """
        Hide unecessary buttons and display correct title
        """
        self.setWindowTitle(self.tr("New connection to {0} network").format(ROOT_SERVERS[currency]["display"]))

    def action_show_pubkey(self):
        salt = self.edit_salt.text()
        password = self.edit_password.text()
        pubkey = SigningKey(salt, password, self.scrypt_params).pubkey
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

    async def show_register_message(self, blockchain_parameters):
        """

        :param sakia.data.entities.BlockchainParameters blockchain_parameters:
        :return:
        """
        days, hours, minutes, seconds = timestamp_to_dhms(blockchain_parameters.idty_window)
        expiration_time_str = self.tr("{days} days, {hours}h  and {min}min").format(days=days,
                                                                                    hours=hours,
                                                                                    min=minutes)

        await QAsyncMessageBox.information(self, self.tr("Registration"), self.tr("""
<b>Congratulations !</b><br>
<br>
You just published your identity to the network.<br>
For your identity to be registered, you will need <b>{certs} certifications</b> from members.<br>
Once you got the required certifications, you will be able to validate your registration
by <b>publishing your membership request !</b><br>
Please notice that your identity document <b>will expire in {expiration_time_str}.</b> If you failed
to get {certs} certifications before this time, the process will have to be restarted from scratch.
""".format(certs=blockchain_parameters.sig_qty, expiration_time_str=expiration_time_str)))
