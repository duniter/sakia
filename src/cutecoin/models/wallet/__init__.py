'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import gnupg
from cutecoin.models.coin import Coin

class Wallet(object):
    '''
    A wallet is list of coins.
    It's only used to sort coins.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.coins = []
        self.currency = ""


    def __eq__(self, other):
        return ( self.currency == other.currency )

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    def refreshCoins(self, community, pgpFingerprint):
        dataList = community.ucoinRequest(lambda : ucoin.hdc.coins.List, ctor_args={'pgp_fingerprint':pgpFingerprint})
        for issaunces in dataList['coins']:
            issuer = issaunces['issuer']
            for coinsIds in issaunces['ids']:
                shortened_id = coinsIds
                coin = Coin(pgpFingerprint, issuer+"-"+shortened_id)
                self.coins.append(coin)

    def getText(self):
        return str(self.value()) + " " + self.currency

    def jsonifyCoinsList(self):
        data = []
        for coin in self.coins:
            data.append({'coin' : coin.getId()})
        return data

    def jsonify(self):
        return {'coins': self.jsonifyCoinsList(),
                'currency': self.currency}


