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


    def __init__(self, coins, community):
        '''
        Constructor
        '''
        self.coins = coins
        self.community = community
        self.name = "Main Wallet"


    @classmethod
    def create(cls, community):
        return cls([], community)

    @classmethod
    def load(cls, jsonData, community):
        coins = []
        for coinData in jsonData['coins']:
            coins.append(Coin.fromId(coinData['coin']))
        return cls(coins, community)



    def __eq__(self, other):
        return ( self.community == other.community )

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    def refreshCoins(self, pgpFingerprint):
        dataList = self.community.ucoinRequest(lambda : ucoin.hdc.coins.List, ctor_args={'pgp_fingerprint':pgpFingerprint})
        for issaunces in dataList['coins']:
            issuer = issaunces['issuer']
            for coinsIds in issaunces['ids']:
                shortened_id = coinsIds
                coin = Coin.fromId(pgpFingerprint, issuer+"-"+shortened_id)
                self.coins.append(coin)

    def getText(self):
        return self.name + " : " + str(self.value()) + " " + self.community.currency

    def jsonifyCoinsList(self):
        data = []
        for coin in self.coins:
            data.append({'coin' : coin.getId()})
        return data

    def jsonify(self):
        return {'coins': self.jsonifyCoinsList(),
                'name': self.name}


