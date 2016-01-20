from PyQt5.QtWidgets import QMenu, QAction, QApplication, QMessageBox
from ucoinpy.documents import Block
from ..member import MemberDialog
from ..contact import ConfigureContactDialog
from ..transfer import TransferMoneyDialog
from ..certification import CertificationDialog
from ...tools.decorators import asyncify
from ...core.transfer import Transfer, TransferState
from ...core.registry import Identity


class ContextMenu(QMenu):
    def __init__(self, parent, app, account, community, password_asker):
        """
        :param PyQt5.QtWidgets.QWidget: the parent widget
        :param sakia.core.Application app: Application instance
        :param sakia.core.Account account: The current account instance
        :param sakia.core.Community community: The community instance
        :param sakia.gui.PasswordAsker password_asker: The password dialog
        """
        super().__init__(parent)
        self._app = app
        self._community = community
        self._account = account
        self._password_asker = password_asker

    @staticmethod
    def _add_identity_actions(menu, identity):
        """
        :param ContextMenu menu: the qmenu to add actions to
        :param Identity identity: the identity
        """
        menu.addSeparator().setText(menu.tr("Identity"))

        informations = QAction(menu.tr("Informations"), menu.parent())
        informations.triggered.connect(lambda checked, i=identity: menu.informations(i))
        menu.addAction(informations)

        add_as_contact = QAction(menu.tr("Add as contact"), menu.parent())
        add_as_contact.triggered.connect(lambda checked,i=identity: menu.add_as_contact(i))
        menu.addAction(add_as_contact)

        send_money = QAction(menu.tr("Send money"), menu.parent())
        send_money.triggered.connect(lambda checked, i=identity: menu.send_money(i))
        menu.addAction(send_money)

        view_wot = QAction(menu.tr("View in Web of Trust"), menu.parent())
        view_wot.triggered.connect(lambda checked, i=identity: menu.view_wot(i))
        menu.addAction(view_wot)

        copy_pubkey = QAction(menu.tr("Copy pubkey to clipboard"), menu.parent())
        copy_pubkey.triggered.connect(lambda checked, i=identity: ContextMenu.copy_pubkey_to_clipboard(i))
        menu.addAction(copy_pubkey)

    @staticmethod
    def _add_transfers_actions(menu, transfer):
        """
        :param ContextMenu menu: the qmenu to add actions to
        :param Transfer transfer: the transfer
        """
        menu.addSeparator().setText(menu.tr("Transfer"))
        if transfer.state in (TransferState.REFUSED, TransferState.TO_SEND):
            send_back = QAction(menu.tr("Send again"), menu.parent())
            send_back.triggered.connect(lambda checked, tr=transfer: menu.send_again(tr))
            menu.addAction(send_back)

            cancel = QAction(menu.tr("Cancel"), menu.parent())
            cancel.triggered.connect(lambda checked, tr=transfer: menu.cancel_transfer(tr))
            menu.addAction(cancel)

        if menu._app.preferences['expert_mode']:
            copy_doc = QAction(menu.tr("Copy raw transaction to clipboard"), menu.parent())
            copy_doc.triggered.connect(lambda checked, tx=transfer: menu.copy_transaction_to_clipboard(tx))
            menu.addAction(copy_doc)

            copy_doc = QAction(menu.tr("Copy transaction block to clipboard"), menu.parent())
            copy_doc.triggered.connect(lambda checked, number=transfer.blockid.number:
                                       menu.copy_block_to_clipboard(number))
            menu.addAction(copy_doc)


    @classmethod
    def from_data(cls, parent, app, account, community, password_asker, data):
        """
        Builds a QMenu from data passed as parameters
        Data can be Identity or Transfer

        :param PyQt5.QtWidgets.QWidget parent: the parent widget
        :param sakia.core.Application app: the application
        :param sakia.core.Application app: Application instance
        :param sakia.core.Account account: The current account instance
        :param sakia.core.Community community: The community instance
        :param sakia.gui.PasswordAsker password_asker: The password dialog
        :param tuple data: a tuple of data to add to the menu
        :rtype: ContextMenu
        """
        menu = cls(parent, app, account, community, password_asker)
        build_actions = {
            Identity: ContextMenu._add_identity_actions,
            Transfer: ContextMenu._add_transfers_actions,
            dict: lambda m, d: None
        }
        for d in data:
            build_actions[type(d)](menu, d)

        return menu

    @staticmethod
    def copy_pubkey_to_clipboard(identity):
        clipboard = QApplication.clipboard()
        clipboard.setText(identity.pubkey)

    def informations(self, identity):
        dialog = MemberDialog(self._app, self._account, self._community, identity)
        dialog.exec_()

    def add_as_contact(self, identity):
        dialog = ConfigureContactDialog.from_identity( self.parent(), self._account, identity)
        dialog.exec_()
        #TODO: Send signal from account to refresh contacts
        # if result == QDialog.Accepted:
        #    self.parent().window().refresh_contacts()

    @asyncify
    async def send_money(self, identity):
        await TransferMoneyDialog.send_money_to_identity(self._app, self._account, self._password_asker,
                                                            self._community, identity)
        #TODO: Send signal from account to refresh transfers
        #self.ui.table_history.model().sourceModel().refresh_transfers()

    def view_wot(self, identity):
        self._app.view_identity_in_wot.emit(identity)

    @asyncify
    async def certify_identity(self, identity):
        await CertificationDialog.certify_identity(self._app, self._account, self._password_asker,
                                             self._community, identity)

    @asyncify
    async def send_again(self, transfer):
        await TransferMoneyDialog.send_transfer_again(self._app, self._app.current_account,
                                     self._password_asker, self._community, transfer)
        #TODO: Send signal from account to refresh transfers
        #self.ui.table_history.model().sourceModel().refresh_transfers()

    def cancel_transfer(self, transfer):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer.cancel()
        #TODO: Send signal from transfer to refresh transfers
        #self.ui.table_history.model().sourceModel().refresh_transfers()

    @asyncify
    async def copy_transaction_to_clipboard(self, tx):
        clipboard = QApplication.clipboard()
        raw_doc = await tx.get_raw_document(self._community)
        clipboard.setText(raw_doc.signed_raw())

    @asyncify
    async def copy_block_to_clipboard(self, number):
        clipboard = QApplication.clipboard()
        block = await self._community.get_block(number)
        if block:
            block_doc = Block.from_signed_raw("{0}{1}\n".format(block['raw'], block['signature']))
            clipboard.setText(block_doc.signed_raw())
