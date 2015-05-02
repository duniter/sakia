'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, QLocale


class WalletsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None
        self.account = None

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None)

    def setSourceModel(self, source_model):
        self.community = source_model.community
        self.account = source_model.account
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
                if isinstance(amount_ref, int):
                    return QLocale().toString(amount_ref)
                else:
                    return QLocale().toString(amount_ref, 'f', 6)

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().columns_types.index('amount'):
                return Qt.AlignRight | Qt.AlignVCenter

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
        self.columns_headers = ('Name', 'Amount', 'Pubkey')
        self.columns_types = ('name', 'amount', 'pubkey')

    @property
    def wallets(self):
        return self.account.wallets

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
        # Only name column is editable
        if index.column() == 0:
            return default_flags | Qt.ItemIsEditable
        return default_flags
