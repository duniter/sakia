'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
import logging


class WalletsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None)

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
        self.account = sourceModel.account
        super().setSourceModel(sourceModel)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_data = self.sourceModel().data(source_index, role)
        if role == Qt.DisplayRole:
            if source_index.column() == self.sourceModel().columns_types.index('pubkey'):
                pubkey = "pub:{0}".format(source_data[:5])
                source_data = pubkey
                return source_data
            if source_index.column() == self.sourceModel().columns_types.index('amount'):
                amount_ref = self.account.units_to_ref(source_data,
                                                        self.community)
                units_ref = self.account.diff_ref_name(self.community.short_currency)

                if type(amount_ref) is int:
                    formatter = "{0} {1}"
                else:
                    formatter = "{0:.2f} {1}"

                return formatter.format(amount_ref, units_ref)
        return source_data


class WalletsTableModel(QAbstractTableModel):

    '''
    A Qt list model to display wallets and edit their names
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super().__init__(parent)
        self.account = account
        self.community = community
        self.columns_types = ('name', 'pubkey', 'amount')

    @property
    def wallets(self):
        return self.account.wallets

    def rowCount(self, parent):
        return len(self.wallets)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.columns_types[section]

    def wallet_data(self, row):
        name = self.wallets[row].name
        amount = self.wallets[row].value(self.community)
        pubkey = self.wallets[row].pubkey

        return (name, pubkey, amount)

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.wallet_data(row)[col]

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            if col == self.columns_types.index('name'):
                self.wallets[row].name = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
