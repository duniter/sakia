from PyQt5.QtWidgets import QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from ucoinpy.documents import Block, Membership
import logging

from ..member import MemberDialog
from ..contact import ConfigureContactDialog
from ..transfer import TransferMoneyDialog
from ..certification import CertificationDialog
from ...tools.decorators import asyncify
from ...core.transfer import Transfer, TransferState
from ...core.registry import Identity
from ...tools.exceptions import MembershipNotFoundError


class ContextMenu(QObject):
    view_identity_in_wot = pyqtSignal(object)

    def __init__(self, qmenu, app, account, community, password_asker):
        """
        :param PyQt5.QtWidgets.QMenu: the qmenu widget
        :param sakia.core.Application app: Application instance
        :param sakia.core.Account account: The current account instance
        :param sakia.core.Community community: The community instance
        :param sakia.gui.PasswordAsker password_asker: The password dialog
        """
        super().__init__()
        self.qmenu = qmenu
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
        menu.qmenu.addSeparator().setText(identity.uid)

        informations = QAction(menu.qmenu.tr("Informations"), menu.qmenu.parent())
        informations.triggered.connect(lambda checked, i=identity: menu.informations(i))
        menu.qmenu.addAction(informations)

        if menu._account.pubkey != identity.pubkey:
            add_as_contact = QAction(menu.qmenu.tr("Add as contact"), menu.qmenu.parent())
            add_as_contact.triggered.connect(lambda checked, i=identity: menu.add_as_contact(i))
            menu.qmenu.addAction(add_as_contact)

        if menu._account.pubkey != identity.pubkey:
            send_money = QAction(menu.qmenu.tr("Send money"), menu.qmenu.parent())
            send_money.triggered.connect(lambda checked, i=identity: menu.send_money(i))
            menu.qmenu.addAction(send_money)

        if menu._account.pubkey != identity.pubkey:
            certify = QAction(menu.tr("Certify identity"), menu.qmenu.parent())
            certify.triggered.connect(lambda checked, i=identity: menu.certify_identity(i))
            menu.qmenu.addAction(certify)

        view_wot = QAction(menu.qmenu.tr("View in Web of Trust"), menu.qmenu.parent())
        view_wot.triggered.connect(lambda checked, i=identity: menu.view_wot(i))
        menu.qmenu.addAction(view_wot)

        copy_pubkey = QAction(menu.qmenu.tr("Copy pubkey to clipboard"), menu.qmenu.parent())
        copy_pubkey.triggered.connect(lambda checked, i=identity: ContextMenu.copy_pubkey_to_clipboard(i))
        menu.qmenu.addAction(copy_pubkey)

        if menu._app.preferences['expert_mode']:
            copy_membership = QAction(menu.qmenu.tr("Copy membership document to clipboard"), menu.qmenu.parent())
            copy_membership.triggered.connect(lambda checked, i=identity: menu.copy_membership_to_clipboard(i))
            menu.qmenu.addAction(copy_membership)

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
        if transfer.state in (TransferState.REFUSED, TransferState.TO_SEND):
            send_back = QAction(menu.qmenu.tr("Send again"), menu.qmenu.parent())
            send_back.triggered.connect(lambda checked, tr=transfer: menu.send_again(tr))
            menu.qmenu.addAction(send_back)

            cancel = QAction(menu.qmenu.tr("Cancel"), menu.qmenu.parent())
            cancel.triggered.connect(lambda checked, tr=transfer: menu.cancel_transfer(tr))
            menu.qmenu.addAction(cancel)

        if menu._app.preferences['expert_mode']:
            copy_doc = QAction(menu.qmenu.tr("Copy raw transaction to clipboard"), menu.qmenu.parent())
            copy_doc.triggered.connect(lambda checked, tx=transfer: menu.copy_transaction_to_clipboard(tx))
            menu.qmenu.addAction(copy_doc)

            if transfer.blockUID:
                copy_doc = QAction(menu.qmenu.tr("Copy transaction block to clipboard"), menu.qmenu.parent())
                copy_doc.triggered.connect(lambda checked, number=transfer.blockUID.number:
                                           menu.copy_block_to_clipboard(number))
                menu.qmenu.addAction(copy_doc)


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
        menu = cls(QMenu(parent), app, account, community, password_asker)
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
        MemberDialog.open_dialog(self._app, self._account, self._community, identity)

    def add_as_contact(self, identity):
        dialog = ConfigureContactDialog.from_identity(self._app, self.parent(), self._account, identity)
        dialog.exec_()

    @asyncify
    async def send_money(self, identity):
        await TransferMoneyDialog.send_money_to_identity(self._app, self._account, self._password_asker,
                                                            self._community, identity)
        self._app.refresh_transfers.emit()

    def view_wot(self, identity):
        self.view_identity_in_wot.emit(identity)

    @asyncify
    async def certify_identity(self, identity):
        await CertificationDialog.certify_identity(self._app, self._account, self._password_asker,
                                             self._community, identity)

    @asyncify
    async def send_again(self, transfer):
        await TransferMoneyDialog.send_transfer_again(self._app, self._app.current_account,
                                     self._password_asker, self._community, transfer)
        self._app.refresh_transfers.emit()

    def cancel_transfer(self, transfer):
        reply = QMessageBox.warning(self.qmenu, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer.cancel()
        self._app.refresh_transfers.emit()

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

    @asyncify
    async def copy_membership_to_clipboard(self, identity):
        """

        :param sakia.core.registry.Identity identity:
        :return:
        """
        clipboard = QApplication.clipboard()
        try:
            membership = await identity.membership(self._community)
            if membership:
                block_number = membership['written']
                block = await self._community.get_block(block_number)
                block_doc = Block.from_signed_raw("{0}{1}\n".format(block['raw'], block['signature']))
                for ms_doc in block_doc.joiners:
                    if ms_doc.issuer == identity.pubkey:
                        clipboard.setText(ms_doc.signed_raw())
        except MembershipNotFoundError:
            logging.debug("Could not find membership")

    @asyncify
    async def copy_selfcert_to_clipboard(self, identity):
        """

        :param sakia.core.registry.Identity identity:
        :return:
        """
        clipboard = QApplication.clipboard()
        selfcert = await identity.selfcert(self._community)
        clipboard.setText(selfcert.signed_raw())
