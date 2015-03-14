'''
Created on 5 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ..core.person import Person
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, \
                        QDateTime, QModelIndex
from PyQt5.QtGui import QColor
import logging


class MembersFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
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
        expiration_col = self.sourceModel().columns_ids.index('expiration')
        expiration_index = self.sourceModel().index(source_index.row(), expiration_col)
        expiration_data = self.sourceModel().data(expiration_index, Qt.DisplayRole)
        current_time = QDateTime().currentDateTime().toMSecsSinceEpoch()
        sig_validity = self.community.parameters['sigValidity']
        warning_expiration_time = int(sig_validity / 3)
        #logging.debug("{0} > {1}".format(current_time, expiration_data))
        will_expire_soon = (current_time > expiration_data*1000 - warning_expiration_time*1000)
        if role == Qt.DisplayRole:
            if source_index.column() == self.sourceModel().columns_ids.index('renew'):
                date = QDateTime.fromTime_t(source_data)
                return date.date()
            if source_index.column() == self.sourceModel().columns_ids.index('expiration'):
                date = QDateTime.fromTime_t(source_data)
                return date.date()
            if source_index.column() == self.sourceModel().columns_ids.index('pubkey'):
                return "pub:{0}".format(source_data[:5])

        if role == Qt.ForegroundRole:
            if will_expire_soon:
                return QColor(Qt.red)
        return source_data


class MembersTableModel(QAbstractTableModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, community, parent=None):
        '''
        Constructor
        '''
        super().__init__(parent)
        self.community = community
        self.columns_titles = {
                               'uid': 'UID',
                               'pubkey': 'Pubkey',
                               'renew': 'Last renew date',
                               'expiration': 'Expiration'}
        self.columns_ids = ('uid', 'pubkey', 'renew', 'expiration')

    @property
    def pubkeys(self):
        return self.community.members_pubkeys()

    def rowCount(self, parent):
        return len(self.pubkeys)

    def columnCount(self, parent):
        return len(self.columns_ids)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            id = self.columns_ids[section]
            return self.columns_titles[id]

    def member_data(self, pubkey):
        person = Person.lookup(pubkey, self.community)
        join_block = person.membership(self.community)['blockNumber']
        join_date = self.community.get_block(join_block).mediantime
        parameters = self.community.parameters
        expiration_date = join_date + parameters['sigValidity']
        return (person.name, pubkey, join_date, expiration_date)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return self.member_data(self.pubkeys[row])[col]

    def person_index(self, pubkey):
        try:
            row = self.pubkeys.index(pubkey)
            index_start = self.index(row, 0)
            index_end = self.index(row, len(self.columns_ids))
            return (index_start, index_end)
        except ValueError:
            return (QModelIndex(), QModelIndex())

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
