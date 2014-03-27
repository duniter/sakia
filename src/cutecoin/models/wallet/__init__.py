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
    def load(cls, json_data, community):
        coins = []
        for coinData in json_data['coins']:
            coins.append(Coin.from_id(coinData['coin']))
        return cls(coins, community)

    def __eq__(self, other):
        return (self.community == other.community)

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    # TODO: Refresh coins when changing current account
    def refreshCoins(self, fingerprint):
        data_list = self.community.network.request(
            ucoin.hdc.coins.List({'pgp_fingerprint': fingerprint}))
        for issaunces in data_list['coins']:
            issuer = issaunces['issuer']
            for coins_ids in issaunces['ids']:
                shortened_id = coins_ids
                coin = Coin.from_id(issuer + "-" + shortened_id)
                self.coins.append(coin)

    def getText(self):
        return self.name + " : " + \
            str(self.value()) + " " + self.community.currency

    def jsonify_coins_list(self):
        data = []
        for coin in self.coins:
            data.append({'coin': coin.get_id()})
        return data

    def jsonify(self):
        return {'coins': self.jsonify_coins_list(),
                'name': self.name}
