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
from cutecoin.core.transfer import Transfer, Received
import logging


class Cache():
    def __init__(self, wallet):
        self.latest_block = 0
        self.wallet = wallet

        self._transfers = []
        self.available_sources = []

    def load_from_json(self, data):
        self._transfers = []
        logging.debug(data)

        data_sent = data['transfers']
        for s in data_sent:
            if s['metadata']['issuer'] == self.wallet.pubkey:
                self._transfers.append(Transfer.load(s))
            else:
                self._transfers.append(Received.load(s))

        for s in data['sources']:
            self.available_sources.append(InputSource.from_inline(s['inline']))

        self.latest_block = data['latest_block']

    def jsonify(self):
        data_transfer = []
        for s in self.transfers:
            data_transfer.append(s.jsonify())

        data_sources = []
        for s in self.available_sources:
            s.index = 0
            data_sources.append({'inline': "{0}\n".format(s.inline())})

        return {'latest_block': self.latest_block,
                'transfers': data_transfer,
                'sources': data_sources}

    @property
    def transfers(self):
        return [t for t in self._transfers if t.state != Transfer.DROPPED]

    def refresh(self, community):
        current_block = 0
        try:
            block_data = community.current_blockid()
            current_block = block_data['number']

            # Lets look if transactions took too long to be validated
            awaiting = [t for t in self._transfers
                        if t.state == Transfer.AWAITING]
            for transfer in awaiting:
                transfer.check_refused(current_block)

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
                signed_raw = "{0}{1}\n".format(block['raw'],
                                               block['signature'])
                try:
                    block_doc = Block.from_signed_raw(signed_raw)
                except:
                    logging.debug("Error in {0}".format(block_number))
                    raise
                metadata = {'block': block_number,
                            'time': block_doc.mediantime}
                for tx in block_doc.transactions:
                    metadata['issuer'] = tx.issuers[0]
                    receivers = [o.pubkey for o in tx.outputs
                                 if o.pubkey != metadata['issuer']]
                    metadata['receiver'] = receivers[0]

                    in_issuers = len([i for i in tx.issuers
                                 if i == self.wallet.pubkey]) > 0
                    if in_issuers:
                        outputs = [o for o in tx.outputs
                                   if o.pubkey != self.wallet.pubkey]
                        amount = 0
                        for o in outputs:
                            amount += o.amount
                        metadata['amount'] = amount

                        awaiting = [t for t in self._transfers
                                    if t.state == Transfer.AWAITING]
                        awaiting_docs = [t.txdoc.signed_raw() for t in awaiting]
                        logging.debug(tx.signed_raw())
                        logging.debug(awaiting_docs)
                        if tx.signed_raw() not in awaiting_docs:
                            transfer = Transfer.create_validated(tx, metadata)
                            self._transfers.append(transfer)
                        else:
                            for transfer in awaiting:
                                transfer.check_registered(tx, metadata)
                    else:
                        outputs = [o for o in tx.outputs
                                   if o.pubkey == self.wallet.pubkey]
                        if len(outputs) > 0:
                            amount = 0
                            for o in outputs:
                                amount += o.amount
                            metadata['amount'] = amount
                            self._transfers.append(Received(tx, metadata))

            if current_block > self.latest_block:
                    self.available_sources = self.wallet.sources(community)

        except NoPeerAvailable:
            return

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
            if currency != 'version':
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

    def show_value(self, community):
        return self.referential(community)

    def relative_value(self, community):
        value = self.value(community)
        ud = community.dividend
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

        time = community.get_block().mediantime
        block_number = community.current_blockid()['number']
        key = None
        logging.debug("Key : {0} : {1}".format(salt, password))
        if self.walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))

        transfer = Transfer.initiate(block_number, time, amount,
                                     key.pubkey, recipient, message)
        self.caches[community.currency]._transfers.append(transfer)

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

        tx.sign([key])
        logging.debug("Transaction : {0}".format(tx.signed_raw()))
        transfer.send(tx, community)

    def sources(self, community):
        data = community.request(bma.tx.Sources,
                                 req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    def transfers(self, community):
        return self.caches[community.currency].transfers

    def jsonify(self):
        return {'walletid': self.walletid,
                'pubkey': self.pubkey,
                'name': self.name}
