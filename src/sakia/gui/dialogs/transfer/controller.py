import asyncio
import logging

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication

from sakia.decorators import asyncify
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from .model import TransferModel
from .view import TransferView


class TransferController(QObject):
    """
    The transfer component controller
    """

    def __init__(self, view, model, search_user, user_information):
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
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.combo_connections.currentIndexChanged.connect(self.change_current_connection)
        self.view.spinbox_amount.valueChanged.connect(self.handle_amount_change)
        self.view.spinbox_relative.valueChanged.connect(self.handle_relative_change)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a transfer component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new Transfer controller
        :rtype: TransferController
        """
        view = TransferView(parent.view if parent else None, None, None)
        model = TransferModel(app)
        transfer = cls(view, model, None, None)

        search_user = SearchUserController.create(transfer, app, "")
        transfer.set_search_user(search_user)

        user_information = UserInformationController.create(transfer, app, "", None)
        transfer.set_user_information(user_information)

        search_user.identity_selected.connect(user_information.search_identity)

        view.set_keys(transfer.model.available_connections())
        return transfer

    @classmethod
    def open_dialog(cls, parent, app, connection):
        dialog = cls.create(parent, app)
        if connection:
            dialog.view.combo_connections.setCurrentText(connection.title())
        dialog.refresh()
        return dialog.exec()

    @classmethod
    async def send_money_to_identity(cls, parent, app, connection, identity):
        dialog = cls.create(parent, app)
        dialog.view.combo_connections.setCurrentText(connection.title())
        dialog.user_information.change_identity(identity)
        dialog.view.edit_pubkey.setText(identity.pubkey)
        dialog.view.radio_pubkey.setChecked(True)

        dialog.refresh()
        return await dialog.async_exec()

    @classmethod
    async def send_transfer_again(cls, parent, app, connection, resent_transfer):
        dialog = cls.create(parent, app)
        dialog.view.combo_connections.setCurrentText(connection.title())
        dialog.view.edit_pubkey.setText(resent_transfer.receiver)
        dialog.view.radio_pubkey.setChecked(True)

        dialog.refresh()
        relative = await dialog.model.quant_to_rel(resent_transfer.metadata['amount'])
        dialog.view.set_spinboxes_parameters(1, resent_transfer.metadata['amount'], relative)
        dialog.view.change_relative_amount(relative)
        dialog.view.change_quantitative_amount(resent_transfer.metadata['amount'])

        account = resent_transfer.metadata['issuer']
        wallet_index = [w.pubkey for w in app.current_account.wallets].index(account)
        dialog.view.combo_connections.setCurrentIndex(wallet_index)
        dialog.view.edit_pubkey.setText(resent_transfer.metadata['receiver'])
        dialog.view.radio_pubkey.setChecked(True)
        dialog.view.edit_message.setText(resent_transfer.metadata['comment'])

        return await dialog.async_exec()

    def set_search_user(self, search_user):
        """

        :param search_user:
        :return:
        """
        self.search_user = search_user
        self.view.set_search_user(search_user.view)

    def set_user_information(self, user_information):
        """

        :param user_information:
        :return:
        """
        self.user_information = user_information
        self.view.set_user_information(user_information.view)

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
        else:
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
        #TODO: Handle other amount base than 0
        amount_base = 0

        logging.debug("Showing password dialog...")
        password = await PasswordAskerDialog(self.model.connection).async_exec()
        if password == "":
            self.view.button_box.setEnabled(True)
            return

        logging.debug("Setting cursor...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        logging.debug("Send money...")
        result, transaction = await self.model.send_money(recipient, password, amount, amount_base, comment)
        if result[0]:
            await self.view.show_success(self.model.notifications(), recipient)
            logging.debug("Restore cursor...")
            QApplication.restoreOverrideCursor()

            # If we sent back a transaction we cancel the first one
            self.model.cancel_previous()
            self.model.app.new_transfer.emit(transaction)
            self.view.accept()
        else:
            await self.view.show_error(self.model.notifications(), result[1])

            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    def reject(self):
        self.view.reject()

    def refresh(self):
        amount = self.model.wallet_value()
        total_text = self.model.localized_amount(amount)
        self.view.refresh_labels(total_text)

        if amount == 0:
            self.view.set_button_box(TransferView.ButtonBoxState.NO_AMOUNT)
        else:
            self.view.set_button_box(TransferView.ButtonBoxState.OK)

        max_relative = self.model.quant_to_rel(amount/100)
        current_base = self.model.current_base()

        self.view.set_spinboxes_parameters(pow(10, current_base), amount, max_relative)

    def handle_amount_change(self, value):
        relative = self.model.quant_to_rel(value)
        self.view.change_relative_amount(relative)
        self.refresh_amount_suffix()

    def refresh_amount_suffix(self):
        self.view.spinbox_amount.setSuffix(" " + self.model.connection.currency)

    def handle_relative_change(self, value):
        amount = self.model.rel_to_quant(value)
        self.view.change_quantitative_amount(amount)

    def change_current_connection(self, index):
        self.model.set_connection(index)
        self.search_user.set_currency(self.model.connection.currency)
        self.user_information.set_currency(self.model.connection.currency)
        self.refresh()

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        self.refresh()
        return future

    def exec(self):
        self.refresh()
        self.view.exec()