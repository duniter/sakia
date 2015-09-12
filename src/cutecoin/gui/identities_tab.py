"""
Created on 2 févr. 2014

@author: inso
"""

import logging
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QAction, QMenu, QDialog, \
                            QAbstractItemView
from ..models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.identities_tab_uic import Ui_IdentitiesTab
from .contact import ConfigureContactDialog
from .member import MemberDialog
from .transfer import TransferMoneyDialog
from .certification import CertificationDialog
import asyncio
from ..core.net.api import bma as qtbma
from ..core.registry import Identity
from ..tools.decorators import asyncify


class IdentitiesTabWidget(QWidget, Ui_IdentitiesTab):

    """
    classdocs
    """
    view_in_wot = pyqtSignal(Identity)

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
        self.button_search.clicked.connect(self.search_text)

    def change_account(self, account, password_asker):
        self.account = account
        self.password_asker = password_asker
        if self.account is None:
            self.community = None

    def change_community(self, community):
        self.community = community
        self.table_identities.model().change_community(community)
        self._async_search_direct_connections()

    def identity_context_menu(self, point):
        index = self.table_identities.indexAt(point)
        model = self.table_identities.model()
        if index.row() < model.rowCount():
            source_index = model.mapToSource(index)
            pubkey_col = model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = self.app.identities_registry.find(pubkey, self.community)
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
            menu.exec_(QCursor.pos())

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

    def send_money_to_identity(self, identity):
        if isinstance(identity, str):
            pubkey = identity
        else:
            pubkey = identity.pubkey
        result = TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        if result == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()

    def certify_identity(self, identity):
        CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    def view_wot(self):
        identity = self.sender().data()
        self.view_in_wot.emit(identity)

    def search_text(self):
        """
        Search text and display found identities
        """
        text = self.edit_textsearch.text()

        if len(text) < 2:
            return False
        else:
            asyncio.async(self._async_execute_search_text(text))

    @asyncio.coroutine
    def _async_execute_search_text(self, text):
        response = yield from self.community.bma_access.future_request(qtbma.wot.Lookup, {'search': text})
        identities = []
        for identity_data in response['results']:
            identity = yield from self.app.identities_registry.future_find(identity_data['pubkey'], self.community)
            identities.append(identity)

        self.edit_textsearch.clear()
        self.refresh_identities(identities)

    @asyncify
    @asyncio.coroutine
    def _async_search_members(self):
        """
        Search members of community and display found members
        """
        if self.community:
            pubkeys = self.community.members_pubkeys()
            identities = []
            for p in pubkeys:
                identities.append(self.app.identities_registry.find(p, self.community))

            self.edit_textsearch.clear()
            self.refresh_identities(identities)

    @asyncify
    @asyncio.coroutine
    def _async_search_direct_connections(self):
        """
        Search members of community and display found members
        """
        if self.account and self.community:
            self_identity = self.account.identity(self.community)
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

    def refresh_identities(self, identities):
        """
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        """
        self.table_identities.model().sourceModel().refresh_identities(identities)
        self.table_identities.resizeColumnsToContents()

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super(IdentitiesTabWidget, self).changeEvent(event)

