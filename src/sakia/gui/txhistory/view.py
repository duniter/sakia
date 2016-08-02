from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QModelIndex
from .txhistory_uic import Ui_TxHistoryWidget
from ...tools.decorators import asyncify, once_at_a_time
from ..widgets.context_menu import ContextMenu


class TxHistoryView(QWidget, Ui_TxHistoryWidget):
    """
    The model of Navigation component
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.busy_balance.hide()

        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.resizeColumnsToContents()
        self.table_history.customContextMenuRequested['QPoint'].connect(self.history_context_menu)

    @once_at_a_time
    @asyncify
    async def history_context_menu(self, point):
        index = self.table_history.indexAt(point)
        model = self.table_history.model()
        if index.isValid() and index.row() < model.rowCount(QModelIndex()):
            source_index = model.mapToSource(index)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                     pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)

            identity = await self.app.identities_registry.future_find(pubkey, self.community)

            transfer = model.sourceModel().transfers()[source_index.row()]
            menu = ContextMenu.from_data(self, self.app, self.account, self.community, self.password_asker,
                                         (identity, transfer))
            menu.view_identity_in_wot.connect(self.view_in_wot)

            # Show the context menu.
            menu.qmenu.popup(QCursor.pos())
