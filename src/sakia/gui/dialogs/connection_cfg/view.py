from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal, Qt
from .connection_cfg_uic import Ui_ConnectionConfigurationDialog
from .congratulation_uic import Ui_CongratulationPopup
from duniterpy.key import SigningKey, ScryptParams
from math import ceil, log
from sakia.gui.widgets import toast
from sakia.helpers import timestamp_to_dhms
from sakia.gui.widgets.dialogs import dialog_async_exec, QAsyncMessageBox
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

    def set_license(self, currency):
        license_text = self.tr("""
<H1> License Ğ1 - v0.2 </H1>
<H2> Money licensing and liability commitment. </H2>

<P>Any certification operation of a new member of Ğ1
must first be accompanied by the transmission of this
 license of the currency Ğ1 whose certifier must ensure
 that it has been studied, understood and accepted by the
 person who will be certified.
</P>
<H4> Production of Units Ğ1 </h4>
<P> Ğ1 occurs via a Universal Dividend (DU) for any human member, which is of the form: </ p>
<Ul>
<Li> 1 DU per person per day </ li>
</Ul>
<div>
<P> The amount of DU is identical each day until the next equinox,
where the DU will then be reevaluated according to the formula: </p>
</div>
<div>
<ul>
<li> DU <sub> day </sub> (the following equinox) = DU <day> (equinox) + c² (M / N) (equinox) / (15778800 seconds)
</Ul>
</div>
<div>
<P> With as parameters: </p>
</div>
<div>
<Ul>
<Li> c = 4.88% / equinox </li>
<Li> UD (0) = 10.00 Ğ1 </li>
</Ul>
</div>
<div>
<P> And as variables: </p>
</div>
<div>
<Ul>
<Li> <em> M </em> the total monetary mass at the equinox </li>
<Li> <em> N </em> the number of members at the equinox </li>
</Ul>
<div>
<H4>Web of Trust</H4>
</div>
<div>
<P> <strong> Warning: </strong> Certifying is not just about making sure you've met the person,
it's ensuring that the community Ğ1 knows the certified person well enough and Duplicate account
made by a person certified by you, or other types of problems (disappearance ...),
by cross-checking that will reveal the problem if necessary. </P>
</div>
<div>
<P> When you are a member of Ğ1 and you are about to certify a new account: </p>
</div>
<div>
<P> <strong> You are assured: </strong> </p>
</div>
<div>
<P> 1 °) The person who declares to manage this public key (new account) and to
have personally checked with him that this is the public key is sufficiently well known
 (not only to know this person visually) that you are about to certify.
 </P>
<P> 2a °) To meet her physically to make sure that it is this person you know who manages this public key. </P>
<P> 2b °) Remotely verify the public person / key link by contacting the person via several different means of communication,
such as social network + forum + mail + video conference + phone (acknowledge voice). </P>
<P> Because if you can hack an email account or a forum account, it will be much harder to imagine hacking four distinct
 means of communication, and mimic the appearance (video) as well as the voice of the person . </P>
<P> However, the 2 °) is preferable to 3 °, whereas the 1 °) is always indispensable in all cases. </P>
<p> 3 °) To have verified with the person concerned that he has indeed generated his Duniter account revocation document,
which will enable him, if necessary, to cancel his account (in case of account theft,
ID, an incorrectly created account, etc.).</p>
</div>
<h4>Abbreviated Web of Trust rules</h4>
<div><p>
Each member has a stock of 100 possible certifications,
which can only be issued at the rate of 1 certification / 5 days.</p>

<p>Valid for 2 months, certification for a new member is definitively adopted only if the certified has
 at least 4 other certifications after these 2 months, otherwise the entry process will have to be relaunched.
</p>

<p>To become a new member of TOC Ğ1 therefore 5 certifications
must be obtained at a distance> 5 of 80% of the TOC sentinels.</p>

<p>A member of the TdC Ğ1 is sentinel when he has received and issued at least Y [N] certifications
where N is the number of members of the TdC and Y [N] = ceiling N ^ (1/5). Examples:</p>

<ul>
<li>For 1024 &lt; N ≤ 3125 we have Y [N] = 5</li>
<li>For 7776 &lt; N ≤ 16807 we have Y [N] = 7</li>
<li>For 59049 &lt; N ≤ 100 000 we have Y [N] = 10</li>
</ul>

<p>Once the new member is part of the TOC Ğ1 his certifications remain valid for 2 years.</p>

<p>To remain a member, you must renew your agreement regularly with your private key (every 12 months)
and make sure you have at least 5 certifications valid after 2 years.</p>

<h4>Software Ğ1 and license Ğ1</h4>

<p>The software Ğ1 allowing users to manage their use of Ğ1 must transmit this license with the software
and all the technical parameters of the currency Ğ1 and TdC Ğ1 which are entered in block 0 of Ğ1.</p>

<p>For more details in the technical details it is possible to consult directly the code of Duniter
which is a free software and also the data of the blockchain Ğ1 by retrieving it via a Duniter instance or node Ğ1.</p>

More information on the Duniter Team website <a href="https://www.duniter.org">https://www.duniter.org</a>
""")
        self.text_license.setText(license_text)

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

        dialog = QDialog(self)
        about_dialog = Ui_CongratulationPopup()
        about_dialog.setupUi(dialog)
        dialog.setWindowTitle("Registration")
        about_dialog.label.setText(self.tr("""
<p><b>Congratulations !</b><br>
<br>
You just published your identity to the network.<br>
For your identity to be registered, you will need<br>
<b>{certs} certifications</b> from members.<br>
Once you got the required certifications, <br>
you will be able to validate your registration<br>
by <b>publishing your membership request !</b><br>
Please notice that your identity document <br>
<b>will expire in {expiration_time_str}.</b><br>
If you failed to get {certs} certifications before this time, <br>
the process will have to be restarted from scratch.</p>
""".format(certs=blockchain_parameters.sig_qty, expiration_time_str=expiration_time_str)))

        await dialog_async_exec(dialog)
