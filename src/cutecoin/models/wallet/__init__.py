'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
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

    def __init__(self, key, currency, name):
        '''
        Constructor
        '''
        self.coins = []
        self.key = key
        self.currency = currency
        self.name = name

    @classmethod
    def create(cls, walletid, currency, name):
        return cls(walletid, currency, name)

    @classmethod
    def load(cls, passwd, json_data):
        walletid = json_data['id']
        name = json_data['name']
        currency = json_data['currency']
        return cls(SigningKey(walletid, passwd), currency, name)

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

    def transactions_received(self):
        pass

    def transactions_sent(self):
        pass

    def get_text(self):
        return "%s : \n \
%d %s \n \
%.2f UD" % (self.name, self.value(), self.currency,
                          self.relative_value())

    def jsonify_nodes_list(self):
        data = []
        for node in self.nodes:
            data.append(node.jsonify())
        return data

    def jsonify(self):
        return {'required_trusts': self.required_trusts,
                'key': self.key,
                'name': self.name,
                'currency': self.currency,
                'nodes': self.jsonify_nodes_list()}
