'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy import PROTOCOL_VERSION
from ucoinpy.api import bma
from nacl.encoding import Base64Encoder
from ucoinpy.documents.transaction import InputSource, OutputSource, Transaction
from ucoinpy.key import SigningKey
from ..tools.exceptions import NotEnoughMoneyError
import logging
import base64


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
        walletid = json_data['walletid']
        pubkey = json_data['pubkey']
        name = json_data['name']
        currency = json_data['currency']
        return cls(walletid, pubkey, currency, name)

    def __eq__(self, other):
        return (self.keyid == other.keyid)

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
        for s in self.sources(community):
            value += s.amount
            s.index = 0
            inputs.append(s)
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

        signing = key.sign(bytes(tx.raw(), 'ascii'), Base64Encoder)
        logging.debug("Signature : {0}".format(str(signing.signature)))
        tx.signatures = [str(signing.signature, 'ascii')]
        logging.debug("Transaction : {0}".format(tx.signed_raw()))
        try:
            community.post(bma.tx.Process,
                                post_args={'transaction': tx.signed_raw()})
        except ValueError as e:
            logging.debug("Error : {0}".format(e))

    def sources(self, community):
        data = community.request(bma.tx.Sources, req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    #TODO: Build a cache of latest transactions
    def transactions_sent(self):
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
