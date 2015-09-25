"""
Created on 2 févr. 2014

@author: inso
"""

import asyncio

from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QAction, QMenu, QDialog, \
                            QAbstractItemView
from ucoinpy.api import bma

from ..models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.identities_tab_uic import Ui_IdentitiesTab
from .contact import ConfigureContactDialog
from .member import MemberDialog
from .transfer import TransferMoneyDialog
from cutecoin.gui.widgets.busy import Busy
from .certification import CertificationDialog
from ..core.registry import Identity
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task


class IdentitiesTabWidget(QWidget, Ui_IdentitiesTab):

    """
    classdocs
    """
    view_in_wot = pyqtSignal(Identity)
    money_sent = pyqtSignal()

    def __init__(self, app):
        """
        Init
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: Password asker dialog
        :return:
        """
        super().__init__()
        self.app = app
        self.community = None
        self.account = None
        self.password_asker = None

        self.setupUi(self)

        identities_model = IdentitiesTableModel(self.community)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_identities.setModel(proxy)
        self.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        self.table_identities.sortByColumn(0, Qt.AscendingOrder)
        self.table_identities.resizeColumnsToContents()

        members_action = QAction(self.tr("Members"), self)
        members_action.triggered.connect(self._async_search_members)
        self.button_search.addAction(members_action)
        direct_connections = QAction(self.tr("Direct connections"), self)
        direct_connections.triggered.connect(self._async_search_direct_connections)
        self.button_search.addAction(direct_connections)
        self.button_search.clicked.connect(self._async_execute_search_text)

        self.busy = Busy(self.table_identities)
        self.busy.hide()

    def cancel_once_tasks(self):
        cancel_once_task(self, self.identity_context_menu)
        cancel_once_task(self, self._async_execute_search_text)
        cancel_once_task(self, self._async_search_members)
        cancel_once_task(self, self._async_search_direct_connections)
        cancel_once_task(self, self.refresh_identities)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()
        self.account = account
        self.password_asker = password_asker
        if self.account is None:
            self.community = None

    def change_community(self, community):
        self.cancel_once_tasks()
        self.community = community
        self.table_identities.model().change_community(community)
        self._async_search_direct_connections()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def identity_context_menu(self, point):
        index = self.table_identities.indexAt(point)
        model = self.table_identities.model()
        if index.row() < model.rowCount():
            source_index = model.mapToSource(index)
            pubkey_col = model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = yield from self.app.identities_registry.future_find(pubkey, self.community)
            menu = QMenu(self)

            informations = QAction(self.tr("Informations"), self)
            informations.triggered.connect(self.menu_informations)
            informations.setData(identity)
            add_contact = QAction(self.tr("Add as contact"), self)
            add_contact.triggered.connect(self.menu_add_as_contact)
            add_contact.setData(identity)

            send_money = QAction(self.tr("Send money"), self)
            send_money.triggered.connect(self.menu_send_money)
            send_money.setData(identity)

            certify = QAction(self.tr("Certify identity"), self)
            certify.triggered.connect(self.menu_certify_member)
            certify.setData(identity)

            view_wot = QAction(self.tr("View in Web of Trust"), self)
            view_wot.triggered.connect(self.view_wot)
            view_wot.setData(identity)

            menu.addAction(informations)
            menu.addAction(add_contact)
            menu.addAction(send_money)
            menu.addAction(certify)
            menu.addAction(view_wot)

            # Show the context menu.
            menu.popup(QCursor.pos())

    def menu_informations(self):
        person = self.sender().data()
        self.identity_informations(person)

    def menu_add_as_contact(self):
        person = self.sender().data()
        self.add_identity_as_contact({'name': person.uid,
                                    'pubkey': person.pubkey})

    def menu_send_money(self):
        person = self.sender().data()
        self.send_money_to_identity(person)

    def menu_certify_member(self):
        person = self.sender().data()
        self.certify_identity(person)

    def identity_informations(self, person):
        dialog = MemberDialog(self.app, self.account, self.community, person)
        dialog.exec_()

    def add_identity_as_contact(self, person):
        dialog = ConfigureContactDialog(self.account, self.window(), person)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    @asyncify
    @asyncio.coroutine
    def send_money_to_identity(self, identity):
        if isinstance(identity, str):
            pubkey = identity
        else:
            pubkey = identity.pubkey
        result = yield from TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        if result == QDialog.Accepted:
            self.money_sent.emit()

    @asyncify
    @asyncio.coroutine
    def certify_identity(self, identity):
        yield from CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    def view_wot(self):
        identity = self.sender().data()
        self.view_in_wot.emit(identity)

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def _async_execute_search_text(self, checked):
        self.busy.show()
        text = self.edit_textsearch.text()
        if len(text) < 2:
            return
        response = yield from self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})
        identities = []
        for identity_data in response['results']:
            identity = yield from self.app.identities_registry.future_find(identity_data['pubkey'], self.community)
            identities.append(identity)

        self.edit_textsearch.clear()
        self.refresh_identities(identities)
        self.busy.hide()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def _async_search_members(self, checked=False):
        """
        Search members of community and display found members
        """
        if self.community:
            self.busy.show()
            pubkeys = yield from self.community.members_pubkeys()
            identities = []
            for p in pubkeys:
                identity = yield from self.app.identities_registry.future_find(p, self.community)
                identities.append(identity)

            self.edit_textsearch.clear()
            self.refresh_identities(identities)
            self.busy.hide()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def _async_search_direct_connections(self, checked=False):
        """
        Search members of community and display found members
        """
        if self.account and self.community:
            try:
                self.busy.show()
                self.refresh_identities([])
                self_identity = yield from self.account.identity(self.community)
                account_connections = []
                certs_of = yield from self_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
                for p in certs_of:
                    account_connections.append(p['identity'])
                certifiers_of = [p for p in account_connections]
                certs_by = yield from self_identity.unique_valid_certified_by(self.app.identities_registry, self.community)
                for p in certs_by:
                    account_connections.append(p['identity'])
                certified_by = [p for p in account_connections
                          if p.pubkey not in [i.pubkey for i in certifiers_of]]
                identities = certifiers_of + certified_by
                self.refresh_identities(identities)
            except NoPeerAvailable:
                pass
            finally:
                self.busy.hide()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def refresh_identities(self, identities):
        """
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        """
        self.busy.show()
        yield from self.table_identities.model().sourceModel().refresh_identities(identities)
        self.table_identities.resizeColumnsToContents()
        self.busy.hide()

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super(IdentitiesTabWidget, self).changeEvent(event)

