"""
Created on 2 févr. 2014

@author: inso
"""

import logging

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QT_TRANSLATE_NOOP, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QAction, QMenu, QDialog, \
                            QAbstractItemView
from ucoinpy.api import bma

from ..models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.identities_tab_uic import Ui_IdentitiesTab
from ..core.registry import Identity, BlockchainState
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from .widgets.context_menu import ContextMenu


class IdentitiesTabWidget(QObject):

    """
    classdocs
    """
    view_in_wot = pyqtSignal(Identity)
    money_sent = pyqtSignal()

    _direct_connections_text = QT_TRANSLATE_NOOP("IdentitiesTabWidget", "Search direct certifications")
    _search_placeholder = QT_TRANSLATE_NOOP("IdentitiesTabWidget", "Research a pubkey, an uid...")

    def __init__(self, app, account=None, community=None, password_asker=None,
                 widget=QWidget, view=Ui_IdentitiesTab):
        """
        Init

        :param sakia.core.app.Application app: Application instance
        :param sakia.core.Account account: The account displayed in the widget
        :param sakia.core.Community community: The community displayed in the widget
        :param sakia.gui.Password_Asker: password_asker: The widget to ask for passwords
        :param class widget: The class of the PyQt5 widget used for this tab
        :param class view: The class of the UI View for this tab
        """
        super().__init__()
        self.widget = widget()
        self.ui = view()
        self.ui.setupUi(self.widget)

        self.app = app
        self.community = community
        self.account = account
        self.password_asker = password_asker

        self.direct_connections = QAction(self.tr(IdentitiesTabWidget._direct_connections_text), self)
        self.ui.edit_textsearch.setPlaceholderText(self.tr(IdentitiesTabWidget._search_placeholder))

        identities_model = IdentitiesTableModel()
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.ui.table_identities.setModel(proxy)
        self.ui.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        self.ui.table_identities.sortByColumn(0, Qt.AscendingOrder)
        self.ui.table_identities.resizeColumnsToContents()
        identities_model.modelAboutToBeReset.connect(lambda: self.ui.table_identities.setEnabled(False))
        identities_model.modelReset.connect(lambda: self.ui.table_identities.setEnabled(True))

        self.direct_connections.triggered.connect(self._async_search_direct_connections)
        self.ui.button_search.addAction(self.direct_connections)
        self.ui.button_search.clicked.connect(self._async_execute_search_text)

    def cancel_once_tasks(self):
        cancel_once_task(self, self.identity_context_menu)
        cancel_once_task(self, self._async_execute_search_text)
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
        self.ui.table_identities.model().change_community(community)
        self._async_search_direct_connections()

    @once_at_a_time
    @asyncify
    async def identity_context_menu(self, point):
        index = self.ui.table_identities.indexAt(point)
        model = self.ui.table_identities.model()
        if index.isValid() and index.row() < model.rowCount():
            source_index = model.mapToSource(index)
            pubkey_col = model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = await self.app.identities_registry.future_find(pubkey, self.community)
            menu = ContextMenu.from_data(self.widget, self.app, self.account, self.community, self.password_asker,
                                         (identity,))

            # Show the context menu.
            menu.qmenu.popup(QCursor.pos())

    @once_at_a_time
    @asyncify
    async def _async_execute_search_text(self, checked):
        cancel_once_task(self, self._async_search_direct_connections)

        self.ui.busy.show()
        text = self.ui.edit_textsearch.text()
        if len(text) < 2:
            return
        try:
            response = await self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})
            identities = []
            for identity_data in response['results']:
                for uid_data in identity_data['uids']:
                    identity = Identity.from_handled_data(uid_data['uid'],
                                                         identity_data['pubkey'],
                                                         uid_data['meta']['timestamp'],
                                                         BlockchainState.BUFFERED)
                    identities.append(identity)

            self.ui.edit_textsearch.clear()
            self.ui.edit_textsearch.setPlaceholderText(text)
            await self.refresh_identities(identities)
        except ValueError as e:
            logging.debug(str(e))
        finally:
            self.ui.busy.hide()

    @once_at_a_time
    @asyncify
    async def _async_search_direct_connections(self, checked=False):
        """
        Search members of community and display found members
        """
        cancel_once_task(self, self._async_execute_search_text)

        if self.account and self.community:
            try:
                self.ui.edit_textsearch.setPlaceholderText(self.tr(IdentitiesTabWidget._search_placeholder))
                await self.refresh_identities([])
                self.ui.busy.show()
                self_identity = await self.account.identity(self.community)
                account_connections = []
                certs_of = await self_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
                for p in certs_of:
                    account_connections.append(p['identity'])
                certifiers_of = [p for p in account_connections]
                certs_by = await self_identity.unique_valid_certified_by(self.app.identities_registry, self.community)
                for p in certs_by:
                    account_connections.append(p['identity'])
                certified_by = [p for p in account_connections
                          if p.pubkey not in [i.pubkey for i in certifiers_of]]
                identities = certifiers_of + certified_by
                self.ui.busy.hide()
                await self.refresh_identities(identities)
            except NoPeerAvailable:
                self.ui.busy.hide()

    async def refresh_identities(self, identities):
        """
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        """
        await self.ui.table_identities.model().sourceModel().refresh_identities(identities)
        self.ui.table_identities.resizeColumnsToContents()

    def retranslateUi(self, widget):
        self.direct_connections.setText(self.tr(IdentitiesTabWidget._direct_connections_text))
        super().retranslateUi(self)

    def resizeEvent(self, event):
        self.ui.busy.resize(event.size())
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

