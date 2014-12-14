'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.documents.transaction import InputSource
from ucoinpy.key import SigningKey
import logging
import gnupg
import json
import time
import hashlib
import importlib
from decimal import Decimal
from cutecoin.models.node import Node
from cutecoin.models.transaction import Transaction
from cutecoin.tools.exceptions import AlgorithmNotImplemented


class Wallet(object):

    '''
    A wallet is list of coins.
    It's only used to sort coins.
    '''

    def __init__(self, walletid, pubkey, currency, name):
        '''
        Constructor
        '''
        self.coins = []
        self.walletid = walletid
        self.pubkey = pubkey
        self.currency = currency
        self.name = name

    @classmethod
    def create(cls, walletid, pubkey, currency, name):
        return cls(walletid, pubkey, currency, name)

    @classmethod
    def load(cls, json_data):
        walletid = json_data['id']
        pubkey = json_data['pubkey']
        name = json_data['name']
        currency = json_data['currency']
        return cls(walletid, currency, name)

    def __eq__(self, other):
        return (self.keyid == other.keyid)

    def relative_value(self, community):
        value = self.value()
        block = community.get_block()
        relative_value = value / float(block['du'])
        return relative_value

    def value(self):
        value = 0

        return value

    def send_money(self, recipient, amount, message):
        pass

    def sources(self, community):
        data = community.request(bma.tx.Sources, req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    #TODO: Build a cache of latest transactions
    def transactions_sent(self):
        return []

    def get_text(self):
        return "%s : \n \
%d %s \n \
%.2f UD" % (self.name, self.value(), self.currency,
                          self.relative_value())

    def jsonify(self):
        return {'walletid': self.walletid,
                'name': self.name,
                'currency': self.currency}
