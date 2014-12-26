'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy import PROTOCOL_VERSION
from ucoinpy.api import bma
from ucoinpy.documents.transaction import InputSource, OutputSource, Transaction
from ucoinpy.key import SigningKey
from ..tools.exceptions import NotEnoughMoneyError
import logging
import base64


class Wallet(object):
    '''
    A wallet is used to manage money with a unique key.
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
        self.inputs_cache = None

    @classmethod
    def create(cls, walletid, pubkey, currency, name):
        return cls(walletid, pubkey, currency, name)

    @classmethod
    def load(cls, json_data):
        walletid = json_data['walletid']
        pubkey = json_data['pubkey']
        name = json_data['name']
        currency = json_data['currency']
        return cls(walletid, pubkey, currency, name)

    def __eq__(self, other):
        return (self.keyid == other.keyid)

    def check_password(self, salt, password):
        key = None
        if self.walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password)
        return (key.pubkey == self.pubkey)

    def relative_value(self, community):
        value = self.value(community)
        ud = community.dividend()
        relative_value = value / float(ud)
        return relative_value

    def value(self, community):
        value = 0
        for s in self.sources(community):
            value += s.amount
        return value

    def tx_inputs(self, amount, community):
        value = 0
        inputs = []
        block = community.request(bma.blockchain.Current)
        sources = self.sources(community)
        if not self.inputs_cache:
            self.inputs_cache = (block['number'], sources)
        elif self.inputs_cache[0] < block['number']:
            self.inputs_cache = (block['number'], sources)

        for s in self.inputs_cache[1]:
            value += s.amount
            s.index = 0
            inputs.append(s)
            self.inputs_cache[1].remove(s)
            if value >= amount:
                return inputs

        raise NotEnoughMoneyError(amount, value)
        return []

    def tx_outputs(self, pubkey, amount, inputs):
        outputs = []
        inputs_value = 0
        for i in inputs:
            logging.debug(i)
            inputs_value += i.amount

        overhead = inputs_value - int(amount)
        outputs.append(OutputSource(pubkey, int(amount)))
        if overhead != 0:
            outputs.append(OutputSource(self.pubkey, overhead))
        return outputs

    def send_money(self, salt, password, community,
                   recipient, amount, message):
        inputs = self.tx_inputs(int(amount), community)
        logging.debug("Inputs : {0}".format(inputs))
        outputs = self.tx_outputs(recipient, amount, inputs)
        logging.debug("Outputs : {0}".format(outputs))
        tx = Transaction(PROTOCOL_VERSION, community.currency,
                         [self.pubkey], inputs,
                         outputs, message, None)
        logging.debug("TX : {0}".format(tx.raw()))
        key = None
        logging.debug("Key : {0} : {1}".format(salt, password))
        if self.walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))

        tx.sign([key])
        logging.debug("Transaction : {0}".format(tx.signed_raw()))
        community.post(bma.tx.Process,
                        post_args={'transaction': tx.signed_raw()})

    def sources(self, community):
        data = community.request(bma.tx.Sources, req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    #TODO: Build a cache of latest transactions
    def transactions_sent(self, community):
        return []

    #TODO: Build a cache of latest transactions
    def transactions_received(self, community):
        return []

    def get_text(self, community):
        return "%s : \n \
%d %s \n \
%.2f UD" % (self.name, self.value(community), self.currency,
                          self.relative_value(community))

    def jsonify(self):
        return {'walletid': self.walletid,
                'pubkey': self.pubkey,
                'name': self.name,
                'currency': self.currency}
