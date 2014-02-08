'''
Created on 7 févr. 2014

@author: inso
'''

from cutecoin.models.wallet import Wallet

class Wallets(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.walletsList = []

    def addWallet(self, currency):
        wallet = Wallet(currency)
        if wallet not in self.walletsList:
            self.walletsList.append(wallet)
        else:
            return self.walletsList.get(wallet)

    def getWallet(self, wallet):
        for w in self.walletsLists:
            if w == wallet:
                return w
        return None
