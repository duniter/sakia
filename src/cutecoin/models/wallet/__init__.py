'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import gnupg
from cutecoin.models.coin import Coin

class Wallet(object):
    '''
    classdocs
    '''


    def __init__(self, currency):
        '''
        Constructor
        '''
        self.coins = []
        self.currency = currency


    def __eq__(self, other):
        return ( self.currency == other.currency )

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    def refreshCoins(self, mainNode, pgpFingerprint):
        ucoin.settings['server'] = mainNode
        ucoin.settings['port'] = mainNode
        dataList = ucoin.hdc.coins.List(pgpFingerprint).get()
        for issaunces in dataList['coins']:
            issuer = issaunces['issuer']
            for coinsIds in issaunces['ids']:
                shortened_id = coinsIds
                coin = Coin(pgpFingerprint, issuer+"-"+shortened_id)
                self.coins.append(coin)

    def getText(self):
        return str(self.value()) + " " + self.currency
