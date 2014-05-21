'''
Created on 2 févr. 2014

@author: inso
'''

import re
import math
import logging
import importlib
from cutecoin.tools.exceptions import AlgorithmNotImplemented


class Coin(object):

    '''
    A coin parsing a regex to read its value
    '''

    def __init__(self, issuer, am_number, coin_number):
        self.issuer = issuer
        self.am_number = am_number
        self.coin_number = coin_number

    @classmethod
    def from_id(cls, wallet, coin_id):
        # Regex to parse the coin id
        regex = "^([A-Z\d]{40})-(\d+)-(\d+)$"
        m = re.search(regex, coin_id)
        issuer = m.group(1)
        am_number = int(m.group(2))
        power = int(m.group(3))
        return cls(issuer, am_number, power)

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def value(self, wallet):
        amendment = wallet.get_amendment(self.am_number)
        if 'CoinAlgo' in amendment:
            coin_algo_name = self.amendment['CoinAlgo']
        else:
            coin_algo_name = 'Base2Draft'

        try:
            module = importlib.import_module("cutecoin.models.coin.algorithms")
            coin_algo_class = getattr(module, coin_algo_name)
            coin_algo = coin_algo_class({})
        except AttributeError:
            raise AlgorithmNotImplemented(coin_algo_name)

        return coin_algo(amendment, self.coin_number)

    def get_id(self):
        return self.issuer + "-" \
            + str(self.am_number) + "-" \
            + str(self.coin_number)
