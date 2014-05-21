'''
Created on 2 févr. 2014

@author: inso
'''

import re
import math
import logging
import ucoin


class Coin(object):

    '''
    A coin parsing a regex to read its value
    '''

    def __init__(self, issuer, am_number, coin_number):
        self.issuer = issuer
        self.am_number = am_number
        self.coin_number = coin_number

    @classmethod
    def from_id(cls, coin_id):
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
        amendment_request = ucoin.hdc.amendments.view.Self(self.am_number)
        amendment = wallet.request(amendment_request)
        return wallet.coin_algo(amendment, self.coin_number)

    def get_id(self):
        return self.issuer + "-" \
            + str(self.am_number) + "-" \
            + str(self.coin_number)
