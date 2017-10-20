import re
import logging

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout

from duniterpy.documents.constants import pubkey_regex
from duniterpy.documents import CRCPubkey
from sakia.data.processors import ConnectionsProcessor
from sakia.decorators import asyncify
from sakia.gui.sub.password_input import PasswordInputController
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from sakia.money import Quantitative
from sakia.gui.widgets.dialogs import dialog_async_exec
from .model import TransferModel
from .view import TransferView


class TransferController(QObject):
    """
    The transfer component controller
    """

    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, view, model, search_user, user_information, password_input):
        """
        Constructor of the transfer component

        :param sakia.gui.dialogs.transfer.view.TransferView: the view
        :param sakia.gui.dialogs.transfer.model.TransferModel model: the model
        """
        super().__init__()
        self.view = view
        self.model = model
        self.search_user = search_user
        self.user_information = user_information
        self.password_input = password_input
        self.password_input.set_info_visible(False)
        self.password_input.password_changed.connect(self.refresh)
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.radio_pubkey.toggled.connect(self.refresh)
        self.view.edit_pubkey.textChanged.connect(self.refresh)
        self.view.combo_connections.currentIndexChanged.connect(self.change_current_connection)
        self.view.spinbox_amount.valueChanged.connect(self.handle_amount_change)
        self.view.spinbox_relative.valueChanged.connect(self.handle_relative_change)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a transfer component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app:
        :return: a new Transfer controller
        :rtype: TransferController
        """
        search_user = SearchUserController.create(None, app)
        user_information = UserInformationController.create(None, app, None)
        password_input = PasswordInputController.create(None, None)

        view = TransferView(parent.view if parent else None,
                            search_user.view, user_information.view, password_input.view)
        model = TransferModel(app)
        transfer = cls(view, model, search_user, user_information, password_input)

        search_user.identity_selected.connect(user_information.search_identity)

        view.set_keys(transfer.model.available_connections())
        view.set_contacts(transfer.model.contacts())
        app.new_connection.connect(view.add_key)
        app.connection_removed.connect(view.remove_key)

        return transfer

    @classmethod
    def integrate_to_main_view(cls, parent, app, connection):
        transfer = cls.create(parent, app)
        transfer.view.combo_connections.setCurrentText(connection.title())
        transfer.view.radio_pubkey.toggle()
        transfer.view.groupbox_connection.hide()
        transfer.view.label_total.hide()
        return transfer

    @classmethod
    def open_transfer_with_pubkey(cls, parent, app, connection, pubkey):
        transfer = cls.create(parent, app)
        transfer.view.groupbox_connection.show()
        if connection:
            transfer.view.combo_connections.setCurrentText(connection.title())
        transfer.view.edit_pubkey.setText(pubkey)
        transfer.view.radio_pubkey.setChecked(True)
        transfer.view.radio_pubkey.toggle()

        transfer.refresh()
        return transfer

    @classmethod
    def send_money_to_pubkey(cls, parent, app, connection, pubkey):
        dialog = QDialog(parent)
        dialog.setWindowTitle(dialog.tr("Transfer"))
        dialog.setLayout(QVBoxLayout(dialog))
        transfer = cls.open_transfer_with_pubkey(parent, app, connection, pubkey)

        dialog.layout().addWidget(transfer.view)
        transfer.accepted.connect(dialog.accept)
        transfer.rejected.connect(dialog.reject)
        return dialog.exec()

    @classmethod
    def send_money_to_identity(cls, parent, app, connection, identity):
        dialog = QDialog(parent)
        dialog.setWindowTitle(dialog.tr("Transfer"))
        dialog.setLayout(QVBoxLayout(dialog))
        transfer = cls.open_transfer_with_pubkey(parent, app, connection, identity.pubkey)

        transfer.view.radio_search.toggle()
        transfer.user_information.change_identity(identity)
        dialog.layout().addWidget(transfer.view)
        transfer.accepted.connect(dialog.accept)
        transfer.rejected.connect(dialog.reject)
        return dialog.exec()

    @classmethod
    def send_transfer_again(cls, parent, app, connection, resent_transfer):
        dialog = QDialog(parent)
        dialog.setWindowTitle(dialog.tr("Transfer"))
        dialog.setLayout(QVBoxLayout(dialog))
        transfer = cls.create(parent, app)
        transfer.view.groupbox_connection.show()
        transfer.view.label_total.show()
        transfer.view.combo_connections.setCurrentText(connection.title())
        transfer.view.edit_pubkey.setText(resent_transfer.receivers[0])
        transfer.view.radio_pubkey.setChecked(True)

        transfer.refresh()

        current_base = transfer.model.current_base()
        current_base_amount = resent_transfer.amount / pow(10, resent_transfer.amount_base - current_base)

        relative = transfer.model.quant_to_rel(current_base_amount / 100)
        transfer.view.set_spinboxes_parameters(current_base_amount / 100, relative)
        transfer.view.change_relative_amount(relative)
        transfer.view.change_quantitative_amount(current_base_amount / 100)

        connections_processor = ConnectionsProcessor.instanciate(app)
        wallet_index = connections_processor.connections().index(connection)
        transfer.view.combo_connections.setCurrentIndex(wallet_index)
        transfer.view.edit_pubkey.setText(resent_transfer.receivers[0])
        transfer.view.radio_pubkey.toggle()
        transfer.view.edit_message.setText(resent_transfer.comment)
        dialog.layout().addWidget(transfer.view)
        transfer.accepted.connect(dialog.accept)
        transfer.rejected.connect(dialog.reject)
        return dialog.exec()

    def valid_crc_pubkey(self):
        if self.view.pubkey_value():
            try:
                crc_pubkey = CRCPubkey.from_str(self.view.pubkey_value())
                return crc_pubkey.is_valid()
            except AttributeError:
                return False
        else:
            return False

    def selected_pubkey(self):
        """
        Get selected pubkey in the widgets of the window
        :return: the current pubkey
        :rtype: str
        """
        pubkey = None

        if self.view.recipient_mode() == TransferView.RecipientMode.SEARCH:
            if self.search_user.current_identity():
                pubkey = self.search_user.current_identity().pubkey
        elif self.view.recipient_mode() == TransferView.RecipientMode.LOCAL_KEY:
            pubkey = self.model.connection_pubkey(self.view.local_key_selected())
        elif self.view.recipient_mode() == TransferView.RecipientMode.CONTACT:
            index = self.view.contact_selected()
            if index >= 0:
                pubkey = self.model.contacts()[index].pubkey
        elif self.view.pubkey_value():
            try:
                crc_pubkey = CRCPubkey.from_str(self.view.pubkey_value())
                if crc_pubkey.is_valid():
                    pubkey = crc_pubkey.pubkey
            except AttributeError:
                result = re.compile("^({0})$".format(pubkey_regex)).match(self.view.pubkey_value())
                if result:
                    pubkey = self.view.pubkey_value()
        return pubkey

    @asyncify
    async def accept(self):
        logging.debug("Accept transfer action...")
        self.view.button_box.setEnabled(False)
        comment = self.view.edit_message.text()

        logging.debug("checking recipient mode...")
        recipient = self.selected_pubkey()
        amount = self.view.spinbox_amount.value() * 100
        amount_base = self.model.current_base()

        logging.debug("Showing password dialog...")
        secret_key, password = self.password_input.get_salt_password()

        logging.debug("Setting cursor...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        logging.debug("Send money...")
        result, transactions = await self.model.send_money(recipient, secret_key, password, amount, amount_base, comment)
        if result[0]:
            await self.view.show_success(self.model.notifications(), recipient)
            logging.debug("Restore cursor...")
            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

            # If we sent back a transaction we cancel the first one
            self.model.cancel_previous()
            for tx in transactions:
                self.model.app.new_transfer.emit(self.model.connection, tx)
            self.view.clear()
            self.rejected.emit()
        else:
            await self.view.show_error(self.model.notifications(), result[1])
            for tx in transactions:
                self.model.app.new_transfer.emit(self.model.connection, tx)

            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    def reject(self):
        self.view.clear()
        self.rejected.emit()

    def refresh(self):
        amount = self.model.wallet_value()
        current_base = self.model.current_base()
        current_base_amount = amount / pow(10, current_base)
        total_text = self.model.localized_amount(amount)
        self.view.refresh_labels(total_text)

        if amount == 0:
            self.view.set_button_box(TransferView.ButtonBoxState.NO_AMOUNT)
        if not self.selected_pubkey():
            if self.view.pubkey_value() and not self.valid_crc_pubkey():
                self.view.set_button_box(TransferView.ButtonBoxState.WRONG_RECIPIENT)
            else:
                self.view.set_button_box(TransferView.ButtonBoxState.NO_RECEIVER)
        elif self.password_input.valid():
            self.view.set_button_box(TransferView.ButtonBoxState.OK)
        else:
            self.view.set_button_box(TransferView.ButtonBoxState.WRONG_PASSWORD)

        max_relative = self.model.quant_to_rel(current_base_amount/100)
        self.view.spinbox_amount.setSuffix(Quantitative.base_str(current_base))

        self.view.set_spinboxes_parameters(current_base_amount / 100, max_relative)

    def handle_amount_change(self, value):
        relative = self.model.quant_to_rel(value)
        self.view.change_relative_amount(relative)
        self.refresh()

    def handle_relative_change(self, value):
        amount = self.model.rel_to_quant(value)
        self.view.change_quantitative_amount(amount)
        self.refresh()

    def change_current_connection(self, index):
        self.model.set_connection(index)
        self.password_input.set_connection(self.model.connection)
        self.refresh()
