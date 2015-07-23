"""
Created on 8 févr. 2014

@author: inso
"""
import asyncio
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, QLocale, pyqtSlot


class WalletsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None
        self.app = None

    @property
    def account(self):
        return self.app.current_account

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None)

    def setSourceModel(self, source_model):
        self.community = source_model.community
        self.app = source_model.app
        super().setSourceModel(source_model)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        return left_data < right_data

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_data = self.sourceModel().data(source_index, role)
        if role == Qt.DisplayRole:
            if source_index.column() == self.sourceModel().columns_types.index('pubkey'):
                pubkey = source_data
                source_data = pubkey
                return source_data
            if source_index.column() == self.sourceModel().columns_types.index('amount'):
                amount_ref = self.account.units_to_ref(source_data, self.community)
                # if referential type is quantitative...
                if self.account.ref_type() == 'q':
                    # display int values
                    return QLocale().toString(float(amount_ref), 'f', 0)
                else:
                    # display float values
                    return QLocale().toString(float(amount_ref), 'f',
                                              self.app.preferences['digits_after_comma'])

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().columns_types.index('amount'):
                return Qt.AlignRight | Qt.AlignVCenter

        return source_data


class WalletsTableModel(QAbstractTableModel):
    """
    A Qt list model to display wallets and edit their names
    """

    def __init__(self, app, community, parent=None):
        """

        :param list of cutecoin.core.wallet.Wallet wallets: The list of wallets to display
        :param cutecoin.core.community.Community community: The community to show
        :param PyQt5.QtCore.QObject parent: The parent widget
        :return: The model
        :rtype: WalletsTableModel
        """
        super().__init__(parent)
        self.app = app
        self.account.wallets_changed.connect(self.refresh_account_wallets)

        self.community = community
        self.columns_headers = (self.tr('Name'),
                                self.tr('Amount'),
                                self.tr('Pubkey'))
        self.columns_types = ('name', 'amount', 'pubkey')

    @property
    def account(self):
        return self.app.current_account

    @property
    def wallets(self):
        return self.account.wallets

    @pyqtSlot()
    def refresh_account_wallets(self):
        """
        Change the current wallets, reconnect the slots
        """
        self.beginResetModel()
        for w in self.account.wallets:
            w.inner_data_changed.connect(lambda: self.refresh_wallet(w))
        self.endResetModel()

    def refresh_wallet(self, wallet):
        """
        Refresh the specified wallet value
        :param cutecoin.core.wallet.Wallet wallet: The wallet to refresh
        """
        index = self.account.wallets.index(wallet)
        if index > 0:
            self.dataChanged.emit(index, index)

    def rowCount(self, parent):
        return len(self.wallets)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if self.columns_types[section] == 'amount':
                return '{:}\n({:})'.format(
                    self.columns_headers[section],
                    self.account.ref_name(self.community.short_currency)
                )
            return self.columns_headers[section]

    def wallet_data(self, row):
        name = self.wallets[row].name
        amount = self.wallets[row].value(self.community)
        pubkey = self.wallets[row].pubkey
        return name, amount, pubkey

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.wallet_data(row)[col]

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            # Change model only if value not empty...
            if col == self.columns_types.index('name') and value:
                self.wallets[row].name = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        default_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        #  Only name column is editable
        if index.column() == 0:
            return default_flags | Qt.ItemIsEditable
        return default_flags
