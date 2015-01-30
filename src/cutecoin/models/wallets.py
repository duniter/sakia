'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt
import logging


class WalletsListModel(QAbstractListModel):

    '''
    A Qt list model to display wallets and edit their names
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super(WalletsListModel, self).__init__(parent)
        self.account = account
        self.wallets = account.wallets
        self.community = community

    def rowCount(self, parent):
        return len(self.wallets)

    def data(self, index, role):
        row = index.row()
        w = self.wallets[row]
        if role == Qt.DisplayRole:
            amount = w.value(self.community)
            ref_amount = self.account.units_to_ref(amount, self.community)
            ref_name = self.account.ref_name(self.community.currency)
            return """{0}
{1} {2}""".format(w.name, ref_amount, ref_name)
        elif role == Qt.EditRole:
            return self.wallets[row].name

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            row = index.row()
            self.wallets[row].name = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
