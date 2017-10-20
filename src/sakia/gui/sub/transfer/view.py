from PyQt5.QtWidgets import QWidget, QDialogButtonBox
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QT_TRANSLATE_NOOP, QRegExp
from .transfer_uic import Ui_TransferMoneyWidget
from enum import Enum
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox


class TransferView(QWidget, Ui_TransferMoneyWidget):
    """
    Transfer component view
    """

    class ButtonBoxState(Enum):
        NO_AMOUNT = 0
        OK = 1
        WRONG_PASSWORD = 2
        NO_RECEIVER = 3
        WRONG_RECIPIENT = 4

    class RecipientMode(Enum):
        PUBKEY = 1
        SEARCH = 2
        LOCAL_KEY = 3
        CONTACT = 4

    _button_box_values = {
        ButtonBoxState.NO_AMOUNT: (False,
                                   QT_TRANSLATE_NOOP("TransferView", "No amount. Please give the transfer amount")),
        ButtonBoxState.OK: (True, QT_TRANSLATE_NOOP("CertificationView", "&Ok")),
        ButtonBoxState.WRONG_PASSWORD: (False, QT_TRANSLATE_NOOP("TransferView", "Please enter correct password")),
        ButtonBoxState.NO_RECEIVER: (False, QT_TRANSLATE_NOOP("TransferView", "Please enter a receiver")),
        ButtonBoxState.WRONG_RECIPIENT: (False, QT_TRANSLATE_NOOP("TransferView", "Incorrect receiver address or pubkey"))

    }

    def __init__(self, parent, search_user_view, user_information_view, password_input_view):
        """

        :param parent:
        :param sakia.gui.sub.search_user.view.SearchUserView search_user_view:
        :param sakia.gui.sub.user_information.view.UserInformationView user_information_view:
        :param sakia.gui.sub.password_input.view.PasswordInputView password_input_view:
        """
        super().__init__(parent)
        self.setupUi(self)

        regexp = QRegExp('^([ a-zA-Z0-9-_:/;*?\[\]\(\)\\\?!^+=@&~#{}|<>%.]{0,255})$')
        validator = QRegExpValidator(regexp)
        self.edit_message.setValidator(validator)

        self.search_user = search_user_view
        self.layout_search_user.addWidget(search_user_view)
        self.search_user.button_reset.hide()
        self.user_information_view = user_information_view
        self.group_box_recipient.layout().addWidget(user_information_view)
        self.password_input = password_input_view
        self.layout_password_input.addWidget(password_input_view)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self._amount_base = 0
        self._currency = ""

        self.radio_to_mode = {
            self.radio_search: TransferView.RecipientMode.SEARCH,
            self.radio_local_key: TransferView.RecipientMode.LOCAL_KEY,
            self.radio_contacts: TransferView.RecipientMode.CONTACT,
            self.radio_pubkey: TransferView.RecipientMode.PUBKEY
        }

        for radio_widget in self.radio_to_mode:
            radio_widget.toggled.connect(lambda c,
                                                radio=self.radio_to_mode[radio_widget]: self.recipient_mode_changed(radio))

    def clear(self):
        self._amount_base = 0
        self.radio_pubkey.setChecked(True)
        self.edit_pubkey.clear()
        self.spinbox_amount.setValue(0)
        self.edit_message.clear()
        self.password_input.clear()
        self.search_user.clear()
        self.user_information_view.clear()

    def recipient_mode(self):
        for radio in self.radio_to_mode:
            if radio.isChecked():
                return self.radio_to_mode[radio]

    def set_contacts(self, contacts_list):
        for contact in contacts_list:
            self.combo_contacts.addItem(contact.name)

    def set_keys(self, connections):
        for conn in connections:
            self.combo_connections.addItem(conn.title())
            self.combo_local_keys.addItem(conn.title())

    def add_key(self, conn):
        self.combo_local_keys.addItem(conn.title())

    def remove_key(self, conn):
        index_local_key = self.combo_local_keys.findText(conn.title())
        self.combo_local_keys.removeItem(index_local_key)

    def local_key_selected(self):
        return self.combo_local_keys.currentIndex()

    def contact_selected(self):
        return self.combo_contacts.currentIndex()

    def set_search_user(self, search_user_view):
        """

        :param sakia.gui.search_user.view.SearchUserView search_user_view:
        :return:
        """
        self.search_user = search_user_view

    def recipient_mode_changed(self, radio):
        """
        :param str radio:
        """
        self.edit_pubkey.setEnabled(radio == TransferView.RecipientMode.PUBKEY)
        self.search_user.setEnabled(radio == TransferView.RecipientMode.SEARCH)
        self.combo_local_keys.setEnabled(radio == TransferView.RecipientMode.LOCAL_KEY)
        self.combo_contacts.setEnabled(radio == TransferView.RecipientMode.CONTACT)

    def change_quantitative_amount(self, amount):
        """
        Change relative amount with signals blocked
        :param amount:
        """
        self.spinbox_amount.blockSignals(True)
        self.spinbox_amount.setValue(amount)
        self.spinbox_amount.blockSignals(False)

    def change_relative_amount(self, relative):
        """
        Change the quantitative amount with signals blocks
        :param relative:
        """
        self.spinbox_relative.blockSignals(True)
        self.spinbox_relative.setValue(relative)
        self.spinbox_relative.blockSignals(False)

    def set_spinboxes_parameters(self, max_quant, max_rel):
        """
        Configure the spinboxes
        It should depend on what the last UD base is
        :param int max_quant:
        :param float max_rel:
        """
        self.spinbox_amount.setMaximum(max_quant)
        self.spinbox_relative.setMaximum(max_rel)

    def refresh_labels(self, total_text):
        """
        Refresh displayed texts
        :param str total_text:
        :param str currency:
        """
        self.label_total.setText("{0}".format(total_text))

    def set_button_box(self, state, **kwargs):
        """
        Set button box state
        :param sakia.gui.transfer.view.TransferView.ButtonBoxState state: the state of te button box
        :param dict kwargs: the values to replace from the text in the state
        :return:
        """
        button_box_state = TransferView._button_box_values[state]
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(button_box_state[0])
        self.button_box.button(QDialogButtonBox.Ok).setText(button_box_state[1].format(**kwargs))

    async def show_success(self, notification, recipient):
        if notification:
            toast.display(self.tr("Transfer"),
                      self.tr("Success sending money to {0}").format(recipient))
        else:
            await QAsyncMessageBox.information(self, self.tr("Transfer"),
                      self.tr("Success sending money to {0}").format(recipient))

    async def show_error(self, notification, error_txt):
        if notification:
            toast.display(self.tr("Transfer"), "Error : {0}".format(error_txt))
        else:
            await QAsyncMessageBox.critical(self, self.tr("Transfer"), error_txt)

    def pubkey_value(self):
        return self.edit_pubkey.text()