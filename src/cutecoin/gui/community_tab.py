"""
Created on 2 févr. 2014

@author: inso
"""

import logging
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QAction, QMenu, QDialog, \
                            QAbstractItemView
from cutecoin.models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.community_tab_uic import Ui_CommunityTabWidget
from cutecoin.gui.contact import ConfigureContactDialog
from cutecoin.gui.member import MemberDialog
from .wot_tab import WotTabWidget
from .transfer import TransferMoneyDialog
from .certification import CertificationDialog
from . import toast
import asyncio
from ..core.net.api import bma as qtbma


class CommunityTabWidget(QWidget, Ui_CommunityTabWidget):

    """
    classdocs
    """

    def __init__(self, app, account, community, password_asker, parent):
        """
        Init
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: Password asker dialog
        :param cutecoin.gui.currency_tab.CurrencyTabWidget parent: TabWidget instance
        :return:
        """
        super().__init__()
        self.parent = parent
        self.app = app
        self.community = community
        self.account = account
        self.password_asker = password_asker

        self.setupUi(self)

        identities_model = IdentitiesTableModel(self.community)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_identities.setModel(proxy)
        self.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        self.table_identities.sortByColumn(0, Qt.AscendingOrder)
        self.table_identities.resizeColumnsToContents()

        self.wot_tab = WotTabWidget(self.app, self.account, self.community, self.password_asker, self)
        self.tabs_information.addTab(self.wot_tab, QIcon(':/icons/wot_icon'), self.tr("Web of Trust"))
        members_action = QAction(self.tr("Members"), self)
        members_action.triggered.connect(self.search_members)
        self.button_search.addAction(members_action)
        direct_connections = QAction(self.tr("Direct connections"), self)
        direct_connections.triggered.connect(self.search_direct_connections)
        self.button_search.addAction(direct_connections)

        self.account.identity(self.community).inner_data_changed.connect(self.handle_account_identity_change)
        self.search_direct_connections()
        self.account.membership_broadcasted.connect(self.handle_membership_broadcasted)
        self.account.revoke_broadcasted.connect(self.handle_revoke_broadcasted)
        self.account.selfcert_broadcasted.connect(self.handle_selfcert_broadcasted)

    def handle_membership_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
        else:
            QMessageBox.information(self, self.tr("Membership"), self.tr("Success sending Membership demand"))

    def handle_revoke_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Revoke"), self.tr("Success sending Revoke demand"))
        else:
            QMessageBox.information(self, self.tr("Revoke"), self.tr("Success sending Revoke demand"))

    def handle_selfcert_broadcasted(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Self Certification"), self.tr("Success sending Self Certification document"))
        else:
            QMessageBox.information(self.tr("Self Certification"), self.tr("Success sending Self Certification document"))

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
        dialog = MemberDialog(none, self.account, self.community, person)
        dialog.exec_()

    def add_identity_as_contact(self, person):
        dialog = ConfigureContactDialog(self.account, self.window(), person)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def send_money_to_identity(self, person):
        if isinstance(person, str):
            pubkey = person
        else:
            pubkey = person.pubkey
        dialog = TransferMoneyDialog(self.app, self.account, self.password_asker)
        dialog.edit_pubkey.setText(pubkey)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.radio_pubkey.setChecked(True)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()

    def certify_identity(self, identity):
        dialog = CertificationDialog(self.account, self.app, self.password_asker)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.radio_pubkey.setChecked(True)
        dialog.exec_()

    def view_wot(self):
        person = self.sender().data()
        # redraw WoT with this identity selected
        self.wot_tab.draw_graph({'text': person.uid, 'id': person.pubkey})
        # change page to WoT
        index_community_tab = self.parent.tabs_account.indexOf(self)
        self.parent.tabs_account.setCurrentIndex(index_community_tab)
        index_wot_tab = self.tabs_information.indexOf(self.wot_tab)
        self.tabs_information.setCurrentIndex(index_wot_tab)

    @asyncio.coroutine
    def _execute_search_text(self, text):
        response = yield from self.community.bma_access.future_request(qtbma.wot.Lookup, {'search': text})
        identities = []
        for identity_data in response['results']:
            identity = yield from self.app.identities_registry.future_find(identity_data['pubkey'], self.community)
            identities.append(identity)

        self_identity = self.account.identity(self.community)
        try:
            self_identity.inner_data_changed.disconnect(self.handle_account_identity_change)
            self.community.inner_data_changed.disconnect(self.handle_community_change)
        except TypeError as e:
            if "disconnect() failed" in str(e):
                pass
            else:
                raise

        self.edit_textsearch.clear()
        self.refresh_identities(identities)

    def search_text(self):
        """
        Search text and display found identities
        """
        text = self.edit_textsearch.text()

        if len(text) < 2:
            return False
        else:
            asyncio.async(self._execute_search_text(text))

    @pyqtSlot(str)
    def handle_community_change(self, origin):
        logging.debug("Handle account community {0}".format(origin))
        if origin == qtbma.wot.Members:
            self.search_members()

    @pyqtSlot(str)
    def handle_account_identity_change(self, origin):
        logging.debug("Handle account identity change {0}".format(origin))
        if origin in (str(qtbma.wot.CertifiedBy), str(qtbma.wot.CertifiersOf)):
            self.search_direct_connections()

    def search_members(self):
        """
        Search members of community and display found members
        """
        pubkeys = self.community.members_pubkeys()
        identities = []
        for p in pubkeys:
            identities.append(self.app.identities_registry.find(p, self.community))

        self_identity = self.account.identity(self.community)

        try:
            self_identity.inner_data_changed.disconnect(self.handle_account_identity_change)
            self.community.inner_data_changed.connect(self.handle_community_change)
        except TypeError as e:
            if "disconnect() failed" in str(e):
                pass
            else:
                raise

        self.edit_textsearch.clear()
        self.refresh_identities(identities)

    def search_direct_connections(self):
        """
        Search members of community and display found members
        """
        self_identity = self.account.identity(self.community)
        try:
            self.community.inner_data_changed.disconnect(self.handle_community_change)
            self_identity.inner_data_changed.connect(self.handle_account_identity_change)
        except TypeError as e:
            if "disconnect() failed" in str(e):
                logging.debug("Could not disconnect community")
            else:
                raise

        account_connections = []
        for p in self_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community):
            account_connections.append(p['identity'])
        certifiers_of = [p for p in account_connections]
        for p in self_identity.unique_valid_certified_by(self.app.identities_registry, self.community):
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

