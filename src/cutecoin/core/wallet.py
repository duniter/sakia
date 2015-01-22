'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy import PROTOCOL_VERSION
from ucoinpy.api import bma
from ucoinpy.documents.block import Block
from ucoinpy.documents.transaction import InputSource, OutputSource, Transaction
from ucoinpy.key import SigningKey
from ..tools.exceptions import NotEnoughMoneyError, NoPeerAvailable
import logging


class Cache():
    def __init__(self, wallet):
        self.latest_block = 0
        self.wallet = wallet

        self.tx_sent = []
        self.awaiting_tx = []
        self.tx_received = []
        self.available_sources = []

    def load_from_json(self, data):
        self.tx_received = []
        self.tx_sent = []
        self.awaiting_tx = []

        data_received = data['received']
        for r in data_received:
            self.tx_received.append(Transaction.from_signed_raw(r['raw']))

        data_sent = data['sent']
        for s in data_sent:
            self.tx_sent.append(Transaction.from_signed_raw(s['raw']))

        data_awaiting = data['awaiting']
        for s in data_awaiting:
            self.awaiting_tx.append(Transaction.from_signed_raw(s['raw']))

        if 'sources' in data:
            data_sources = data['sources']
            for s in data_sources:
                self.available_sources.append(InputSource.from_inline(s['inline']))

        self.latest_block = data['latest_block']

    def jsonify(self):
        data_received = []
        for r in self.tx_received:
            data_received.append({'raw': r.signed_raw()})

        data_sent = []
        for s in self.tx_sent:
            data_sent.append({'raw': s.signed_raw()})

        data_awaiting = []
        for s in self.awaiting_tx:
            data_awaiting.append({'raw': s.signed_raw()})

        data_sources = []
        for s in self.available_sources:
            s.index = 0
            data_sources.append({'inline': "{0}\n".format(s.inline())})

        return {'latest_block': self.latest_block,
                'received': data_received,
                'sent': data_sent,
                'awaiting': data_awaiting,
                'sources': data_sources}

    def latest_sent(self, community):
        return self.tx_sent

    def awaiting(self, community):
        return self.awaiting_tx

    def latest_received(self, community):
        return self.tx_received

    def refresh(self, community):
        current_block = 0
        try:
            try:
                block_data = community.request(bma.blockchain.Current)
                current_block = block_data['number']
            except ValueError as e:
                if '404' in str(e):
                    current_block = 0
                else:
                    raise
            with_tx = community.request(bma.blockchain.TX)

            # We parse only blocks with transactions
            parsed_blocks = reversed(range(self.latest_block + 1,
                                               current_block + 1))
            logging.debug("Refresh from {0} to {1}".format(self.latest_block + 1,
                                               current_block + 1))
            parsed_blocks = [n for n in parsed_blocks
                             if n in with_tx['result']['blocks']]

            for block_number in parsed_blocks:
                block = community.request(bma.blockchain.Block,
                                  req_args={'number': block_number})
                signed_raw = "{0}{1}\n".format(block['raw'], block['signature'])
                block_doc = Block.from_signed_raw(signed_raw)
                for tx in block_doc.transactions:
                    in_outputs = [o for o in tx.outputs
                                  if o.pubkey == self.wallet.pubkey]
                    if len(in_outputs) > 0:
                        self.tx_received.append(tx)

                    in_inputs = [i for i in tx.issuers if i == self.wallet.pubkey]
                    if len(in_inputs) > 0:
                        # remove from waiting transactions list the one which were
                        # validated in the blockchain
                        self.awaiting_tx = [awaiting for awaiting in self.awaiting_tx
                                             if awaiting.compact() != tx.compact()]
                        self.tx_sent.append(tx)

            if current_block > self.latest_block:
                    self.available_sources = self.wallet.sources(community)

        except NoPeerAvailable:
            return

        self.tx_sent = self.tx_sent[:50]
        self.tx_received = self.tx_received[:50]

        self.latest_block = current_block


class Wallet(object):
    '''
    A wallet is used to manage money with a unique key.
    '''

    def __init__(self, walletid, pubkey, name):
        '''
        Constructor
        '''
        self.coins = []
        self.walletid = walletid
        self.pubkey = pubkey
        self.name = name
        self.caches = {}

    @classmethod
    def create(cls, walletid, salt, password, name):
        if walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, walletid), password)
        return cls(walletid, key.pubkey, name)

    @classmethod
    def load(cls, json_data):
        walletid = json_data['walletid']
        pubkey = json_data['pubkey']
        name = json_data['name']
        return cls(walletid, pubkey, name)

    def __eq__(self, other):
        return (self.keyid == other.keyid)

    def load_caches(self, json_data):
        for currency in json_data:
            self.caches[currency] = Cache(self)
            self.caches[currency].load_from_json(json_data[currency])

    def jsonify_caches(self):
        data = {}
        for currency in self.caches:
            data[currency] = self.caches[currency].jsonify()
        return data

    def refresh_cache(self, community):
        if community.currency not in self.caches:
            self.caches[community.currency] = Cache(self)
        self.caches[community.currency].refresh(community)

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
        cache = self.caches[community.currency]

        logging.debug("Available inputs : {0}".format(cache.available_sources))
        buf_inputs = list(cache.available_sources)
        for s in cache.available_sources:
            value += s.amount
            s.index = 0
            inputs.append(s)
            buf_inputs.remove(s)
            if value >= amount:
                return (inputs, buf_inputs)

        raise NotEnoughMoneyError(value, community.currency,
                                  len(inputs), amount)

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

        result = self.tx_inputs(int(amount), community)
        inputs = result[0]
        self.caches[community.currency].available_sources = result[1]
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
        try:
            community.broadcast(bma.tx.Process,
                        post_args={'transaction': tx.signed_raw()})
            self.caches[community.currency].awaiting_tx.append(tx)
        except:
            raise

    def sources(self, community):
        data = community.request(bma.tx.Sources,
                                 req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    def transactions_awaiting(self, community):
        return self.caches[community.currency].awaiting(community)

    def transactions_sent(self, community):
        return self.caches[community.currency].latest_sent(community)

    def transactions_received(self, community):
        return self.caches[community.currency].latest_received(community)

    def get_text(self, community):
        return "%s : \n \
%d %s \n \
%.2f UD" % (self.name, self.value(community), community.currency,
                          self.relative_value(community))

    def jsonify(self):
        return {'walletid': self.walletid,
                'pubkey': self.pubkey,
                'name': self.name}
