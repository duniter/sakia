import logging

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction, QApplication, QMessageBox

from sakia.data.entities import Identity, Transaction, Dividend
from sakia.data.processors import BlockchainProcessor, TransactionsProcessor
from sakia.decorators import asyncify
from sakia.gui.dialogs.certification.controller import CertificationController
from sakia.gui.sub.transfer.controller import TransferController
from sakia.gui.sub.user_information.controller import UserInformationController


class ContextMenu(QObject):
    view_identity_in_wot = pyqtSignal(object)
    identity_information_loaded = pyqtSignal(Identity)

    def __init__(self, qmenu, app, connection):
        """
        :param PyQt5.QtWidgets.QMenu: the qmenu widget
        :param sakia.app.Application app: Application instance
        :param sakia.data.entities.Connection connection: The current connection instance
        """
        super().__init__()
        self.qmenu = qmenu
        self._app = app
        self._connection = connection

    @staticmethod
    def _add_identity_actions(menu, identity):
        """
        :param ContextMenu menu: the qmenu to add actions to
        :param Identity identity: the identity
        """
        menu.qmenu.addSeparator().setText(identity.uid if identity.uid else "Pubkey")

        informations = QAction(menu.qmenu.tr("Informations"), menu.qmenu.parent())
        informations.triggered.connect(lambda checked, i=identity: menu.informations(i))
        menu.qmenu.addAction(informations)

        if menu._connection.pubkey != identity.pubkey:
            send_money = QAction(menu.qmenu.tr("Send money"), menu.qmenu.parent())
            send_money.triggered.connect(lambda checked, i=identity: menu.send_money(i))
            menu.qmenu.addAction(send_money)

        if identity.uid and menu._connection.pubkey != identity.pubkey:
            certify = QAction(menu.tr("Certify identity"), menu.qmenu.parent())
            certify.triggered.connect(lambda checked, i=identity: menu.certify_identity(i))
            menu.qmenu.addAction(certify)

        view_wot = QAction(menu.qmenu.tr("View in Web of Trust"), menu.qmenu.parent())
        view_wot.triggered.connect(lambda checked, i=identity: menu.view_wot(i))
        menu.qmenu.addAction(view_wot)

        copy_pubkey = QAction(menu.qmenu.tr("Copy pubkey to clipboard"), menu.qmenu.parent())
        copy_pubkey.triggered.connect(lambda checked, i=identity: ContextMenu.copy_pubkey_to_clipboard(i))
        menu.qmenu.addAction(copy_pubkey)

        if identity.uid and menu._app.parameters.expert_mode:
            copy_selfcert = QAction(menu.qmenu.tr("Copy self-certification document to clipboard"), menu.qmenu.parent())
            copy_selfcert.triggered.connect(lambda checked, i=identity: menu.copy_selfcert_to_clipboard(i))
            menu.qmenu.addAction(copy_selfcert)

    @staticmethod
    def _add_transfers_actions(menu, transfer):
        """
        :param ContextMenu menu: the qmenu to add actions to
        :param Transfer transfer: the transfer
        """
        menu.qmenu.addSeparator().setText(menu.qmenu.tr("Transfer"))
        if transfer.state in (Transaction.REFUSED, Transaction.TO_SEND):
            send_back = QAction(menu.qmenu.tr("Send again"), menu.qmenu.parent())
            send_back.triggered.connect(lambda checked, tr=transfer: menu.send_again(tr))
            menu.qmenu.addAction(send_back)

            cancel = QAction(menu.qmenu.tr("Cancel"), menu.qmenu.parent())
            cancel.triggered.connect(lambda checked, tr=transfer: menu.cancel_transfer(tr))
            menu.qmenu.addAction(cancel)

        if menu._app.parameters.expert_mode:
            copy_doc = QAction(menu.qmenu.tr("Copy raw transaction to clipboard"), menu.qmenu.parent())
            copy_doc.triggered.connect(lambda checked, tx=transfer: menu.copy_transaction_to_clipboard(tx))
            menu.qmenu.addAction(copy_doc)

            if transfer.blockstamp:
                copy_doc = QAction(menu.qmenu.tr("Copy transaction block to clipboard"), menu.qmenu.parent())
                copy_doc.triggered.connect(lambda checked, number=transfer.blockstamp.number:
                                           menu.copy_block_to_clipboard(transfer.blockstamp.number))
                menu.qmenu.addAction(copy_doc)

    @classmethod
    def from_data(cls, parent, app, connection, data):
        """
        Builds a QMenu from data passed as parameters
        Data can be Identity or Transfer

        :param PyQt5.QtWidgets.QWidget parent: the parent widget
        :param sakia.app.Application app: Application instance
        :param sakia.data.entities.Connection connection: the current connection
        :param tuple data: a tuple of data to add to the menu
        :rtype: ContextMenu
        """
        menu = cls(QMenu(parent), app, connection)
        build_actions = {
            Identity: ContextMenu._add_identity_actions,
            Transaction: ContextMenu._add_transfers_actions,
            Dividend: lambda m, d: None,
            dict: lambda m, d: None,
            type(None): lambda m, d: None
        }
        for d in data:
            build_actions[type(d)](menu, d)

        return menu

    @staticmethod
    def copy_pubkey_to_clipboard(identity):
        clipboard = QApplication.clipboard()
        clipboard.setText(identity.pubkey)

    def informations(self, identity):
        if identity.uid:
            UserInformationController.show_identity(self.parent(), self._app, identity)
            self.identity_information_loaded.emit(identity)
        else:
            UserInformationController.search_and_show_pubkey(self.parent(), self._app,
                                                             identity.pubkey)

    @asyncify
    async def send_money(self, identity):
        await TransferController.send_money_to_identity(None, self._app, self._connection, identity)

    def view_wot(self, identity):
        self.view_identity_in_wot.emit(identity)

    @asyncify
    async def certify_identity(self, identity):
        await CertificationController.certify_identity(None, self._app, self._connection, identity)

    def send_again(self, transfer):
        TransferController.send_transfer_again(None, self._app, self._connection, transfer)

    def cancel_transfer(self, transfer):
        reply = QMessageBox.warning(self.qmenu, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transactions_processor = TransactionsProcessor.instanciate(self._app)
            if transactions_processor.cancel(transfer):
                self._app.sources_service.restore_sources(self._connection.pubkey, transfer)
            self._app.db.commit()
            self._app.transaction_state_changed.emit(transfer)

    def copy_transaction_to_clipboard(self, tx):
        clipboard = QApplication.clipboard()
        clipboard.setText(tx.raw)

    @asyncify
    async def copy_block_to_clipboard(self, number):
        clipboard = QApplication.clipboard()
        blockchain_processor = BlockchainProcessor.instanciate(self._app)
        block_doc = await blockchain_processor.get_block(self._connection.currency, number)
        clipboard.setText(block_doc.signed_raw())

    @asyncify
    async def copy_selfcert_to_clipboard(self, identity):
        """

        :param sakia.core.registry.Identity identity:
        :return:
        """
        clipboard = QApplication.clipboard()
        selfcert = await identity.selfcert(self._community)
        clipboard.setText(selfcert.signed_raw())
