from sakia.gui.component.controller import ComponentController
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from .view import TransferView
from .model import TransferModel
from sakia.tools.decorators import asyncify
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import logging
import asyncio


class TransferController(ComponentController):
    """
    The transfer component controller
    """

    def __init__(self, parent, view, model, search_user, user_information, password_asker):
        """
        Constructor of the transfer component

        :param sakia.gui.transfer.view.TransferView: the view
        :param sakia.gui.transfer.model.TransferModel model: the model
        """
        super().__init__(parent, view, model)
        self.password_asker = password_asker
        self.search_user = search_user
        self.user_information = user_information
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.combo_community.currentIndexChanged.connect(self.change_current_community)
        self.view.combo_wallets.currentIndexChanged.connect(self.change_current_wallet)
        self.view.spinbox_amount.valueChanged.connect(self.handle_amount_change)
        self.view.spinbox_relative.valueChanged.connect(self.handle_relative_change)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a transfer component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new Transfer controller
        :rtype: TransferController
        """
        account = kwargs['account']
        community = kwargs['community']
        transfer = kwargs['transfer']
        password_asker = kwargs['password_asker']
        communities_names = [c.name for c in account.communities]
        wallets_names = [w.name for w in account.wallets]
        contacts_names = [c['name'] for c in account.contacts]

        view = TransferView(parent.view, None, None, communities_names, contacts_names, wallets_names)
        model = TransferModel(None, app, account=account, community=community, resent_transfer=transfer)
        transfer = cls(parent, view, model, None, None, password_asker)

        search_user = SearchUserController.create(transfer, app,
                                                  account=model.account,
                                                  community=model.community)
        transfer.set_search_user(search_user)

        user_information = UserInformationController.create(transfer, app,
                                                            account=model.account,
                                                            community=model.community,
                                                            identity=None)
        transfer.set_user_information(user_information)
        model.setParent(transfer)
        return transfer

    @classmethod
    def open_dialog(cls, parent, app, account, password_asker, community):
        dialog = cls.create(parent, app,
                     account=account,
                     password_asker=password_asker,
                     community=community,
                     transfer=None)
        return dialog.exec()

    @classmethod
    async def send_money_to_identity(cls, parent, app, account, password_asker, community, identity):
        dialog = cls.create(parent, app,
                     account=account,
                     password_asker=password_asker,
                     community=community,
                     transfer=None)
        dialog.view.edit_pubkey.setText(identity.pubkey)
        dialog.view.radio_pubkey.setChecked(True)
        return await dialog.async_exec()

    @classmethod
    async def send_transfer_again(cls, parent, app, account, password_asker, community, resent_transfer):
        dialog = cls.create(parent, app,
                            account=account,
                            password_asker=password_asker,
                            community=community,
                            resent_transfer=resent_transfer)
        relative = await dialog.model.quant_to_rel(resent_transfer.metadata['amount'])
        dialog.view.set_spinboxes_parameters(1, resent_transfer.metadata['amount'], relative)
        dialog.view.change_relative_amount(relative)
        dialog.view.change_quantitative_amount(resent_transfer.metadata['amount'])

        account = resent_transfer.metadata['issuer']
        wallet_index = [w.pubkey for w in app.current_account.wallets].index(account)
        dialog.view.combo_wallets.setCurrentIndex(wallet_index)
        dialog.view.edit_pubkey.setText(resent_transfer.metadata['receiver'])
        dialog.view.radio_pubkey.setChecked(True)
        dialog.view.edit_message.setText(resent_transfer.metadata['comment'])

        return await dialog.async_exec()

    @property
    def view(self) -> TransferView:
        return self._view

    @property
    def model(self) -> TransferModel:
        return self._model

    def set_search_user(self, search_user):
        """

        :param search_user:
        :return:
        """
        self.search_user = search_user
        self.view.set_search_user(search_user.view)
        search_user.identity_selected.connect(self.refresh_user_information)

    def set_user_information(self, user_information):
        """

        :param user_information:
        :return:
        """
        self.user_information = user_information
        self.view.set_user_information(user_information.view)

    def refresh_user_information(self):
        """
        Refresh user information
        """
        pubkey = self.selected_pubkey()
        self.user_information.search_identity(pubkey)

    def selected_pubkey(self):
        """
        Get selected pubkey in the widgets of the window
        :return: the current pubkey
        :rtype: str
        """
        pubkey = None

        if self.view.recipient_mode() == TransferView.RecipientMode.CONTACT:
            contact_name = self.view.selected_contact()
            pubkey = self.model.contact_name_pubkey(contact_name)
        elif self.view.recipient_mode() == TransferView.RecipientMode.SEARCH:
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
        amount = self.view.spinbox_amount.value()

        logging.debug("Showing password dialog...")
        password = await self.password_asker.async_exec()
        if password == "":
            self.view.button_box.setEnabled(True)
            return

        logging.debug("Setting cursor...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        logging.debug("Send money...")
        result = await self.model.send_money(recipient, amount, comment, password)
        if result[0]:
            await self.view.show_success(self.model.app.preferences['notifications'], recipient)
            logging.debug("Restore cursor...")
            QApplication.restoreOverrideCursor()

            # If we sent back a transaction we cancel the first one
            self.model.cancel_previous()
            self.model.app.refresh_transfers.emit()
            self.view.accept()
        else:
            await self.view.show_error(self.model.app.preferences['notifications'], result[1])

            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    def reject(self):
        self.view.reject()

    @asyncify
    async def refresh(self):
        amount = await self.model.wallet_value()
        total_text = await self.model.localized_amount(amount)
        self.view.refresh_labels(total_text, self.model.community.currency)

        if amount == 0:
            self.view.set_button_box(TransferView.ButtonBoxState.NO_AMOUNT)
        else:
            self.view.set_button_box(TransferView.ButtonBoxState.OK)

        max_relative = await self.model.quant_to_rel(amount)
        current_base = await self.model.current_base()

        self.view.set_spinboxes_parameters(pow(10, current_base), amount, max_relative)

    @asyncify
    async def handle_amount_change(self, value):
        relative = await self.model.quant_to_rel(value)
        self.view.change_relative_amount(relative)

    @asyncify
    async def handle_relative_change(self, value):
        amount = await self.model.rel_to_quant(value)
        self.view.change_quantitative_amount(amount)

    def change_current_community(self, index):
        self.model.change_community(index)
        self.search_user.set_community(self.community)
        self.user_information.change_community(self.community)
        self.refresh()

    def change_current_wallet(self, index):
        self.model.change_wallet(index)
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