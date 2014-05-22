'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt


class CoinsListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, wallet, coins, parent=None):
        '''
        Constructor
        '''
        super(CoinsListModel, self).__init__(parent)
        self.sorted_coins = {}
        self.coin_values = set()
        for c in coins:
            value = c.value(wallet)

            if value not in self.sorted_coins:
                self.sorted_coins[value] = []

            self.sorted_coins[value] += [c]
            self.coin_values.update([value])

        self.ordered_values = list(self.coin_values)
        self.ordered_values.sort()
        self.wallet = wallet

    def rowCount(self, parent):
        return len(self.ordered_values)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            coins_list = self.sorted_coins[self.ordered_values[row]]

            text = """%d coins of %d""" % (len(coins_list),
                                           self.ordered_values[row])
            return text

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def remove_coins(self, index, number):
        removed = []
        value = self.ordered_values[index.row()]
        removed += self.sorted_coins[value][-number:]
        self.sorted_coins[value] = self.sorted_coins[value][:-number]
        self.dataChanged.emit(index, index, [Qt.DisplayRole])
        return removed

    def add_coins(self, coins):
        for c in coins:
            value = c.value(self.wallet)
            if value not in self.sorted_coins:
                self.sorted_coins[value] = []
            self.sorted_coins[value] += [c]
            self.coin_values.update([value])
            self.ordered_values = list(self.coin_values)
            self.ordered_values.sort()
        self.layoutChanged.emit()

    def to_list(self):
        coins_list = []
        for value in self.coin_values:
            for coin in self.sorted_coins[value]:
                coins_list.append(coin.get_id())
        return coins_list

    def total(self):
        total = 0
        for value in self.coin_values:
            for coin in self.sorted_coins[value]:
                total += coin.value(self.wallet)
        return total
