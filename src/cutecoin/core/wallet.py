'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.documents.transaction import InputSource, OutputSource, Transaction
from ucoinpy.key import SigningKey

from .net.api import bma as qtbma
from ..tools.exceptions import NotEnoughMoneyError, NoPeerAvailable, PersonNotFoundError
from .transfer import Transfer, Received
from .person import Person

from PyQt5.QtCore import QObject, pyqtSignal

import logging


class Cache():
    def __init__(self, wallet):
        self._latest_block = 0
        self.wallet = wallet

        self._transfers = []
        self.available_sources = []

    @property
    def latest_block(self):
        return self._latest_block

    @latest_block.setter
    def latest_block(self, value):
        self._latest_block = value

    def load_from_json(self, data):
        self._transfers = []

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

    def _parse_transaction(self, community, tx, block_number,
                           mediantime, received_list, txid):
        #logging.debug(tx.signed_raw())
        receivers = [o.pubkey for o in tx.outputs
                     if o.pubkey != tx.issuers[0]]

        if len(receivers) == 0:
            receivers = [tx.issuers[0]]

        try:
            issuer_uid = Person.lookup(tx.issuers[0], community).uid
        except PersonNotFoundError:
            issuer_uid = ""

        try:
            receiver_uid = Person.lookup(receivers[0], community).uid
        except PersonNotFoundError:
            receiver_uid = ""

        metadata = {'block': block_number,
                    'time': mediantime,
                    'comment': tx.comment,
                    'issuer': tx.issuers[0],
                    'issuer_uid': issuer_uid,
                    'receiver': receivers[0],
                    'receiver_uid': receiver_uid,
                    'txid': txid}

        in_issuers = len([i for i in tx.issuers
                     if i == self.wallet.pubkey]) > 0
        in_outputs = len([o for o in tx.outputs
                       if o.pubkey == self.wallet.pubkey]) > 0

        # If the wallet pubkey is in the issuers we sent this transaction
        if in_issuers:
            outputs = [o for o in tx.outputs
                       if o.pubkey != self.wallet.pubkey]
            amount = 0
            for o in outputs:
                amount += o.amount
            metadata['amount'] = amount

            awaiting = [t for t in self._transfers
                        if t.state == Transfer.AWAITING]
            # We check if the transaction correspond to one we sent
            if tx.signed_raw() not in [t.txdoc.signed_raw() for t in awaiting]:
                transfer = Transfer.create_validated(tx,
                                                     metadata.copy())
                self._transfers.append(transfer)
        # If we are not in the issuers,
        # maybe it we are in the recipients of this transaction
        elif in_outputs:
            outputs = [o for o in tx.outputs
                       if o.pubkey == self.wallet.pubkey]
            amount = 0
            for o in outputs:
                amount += o.amount
            metadata['amount'] = amount
            received = Received(tx, metadata.copy())
            received_list.append(received)
            self._transfers.append(received)


    def _parse_block(self, community, block_number, received_list):
        block = community.request(bma.blockchain.Block,
                                  req_args={'number': block_number})
        signed_raw = "{0}{1}\n".format(block['raw'],
                                       block['signature'])
        try:
            block_doc = Block.from_signed_raw(signed_raw)
        except:
            logging.debug("Error in {0}".format(block_number))
            raise
        for (txid, tx) in enumerate(block_doc.transactions):
            self._parse_transaction(community, tx, block_number,
                                    block_doc.mediantime, received_list,
                                    txid)

        logging.debug("Received {0} transactions".format(len(received_list)))
        awaiting = [t for t in self._transfers
                    if t.state == Transfer.AWAITING]
        # After we checked all transactions, we check if
        # sent transactions still waiting for validation
        # have to be considered refused
        for transfer in awaiting:
            transfer.check_registered(tx, block_number,
                                      block_doc.mediantime)

    def refresh(self, community, received_list):
        current_block = 0
        try:
            block_data = community.current_blockid()
            current_block = block_data['number']

            # Lets look if transactions took too long to be validated
            awaiting = [t for t in self._transfers
                        if t.state == Transfer.AWAITING]
            with_tx = community.request(bma.blockchain.TX)

            # We parse only blocks with transactions
            parsed_blocks = reversed(range(self.latest_block + 1,
                                               current_block + 1))
            logging.debug("Refresh from {0} to {1}".format(self.latest_block + 1,
                                               current_block + 1))
            parsed_blocks = [n for n in parsed_blocks
                             if n in with_tx['result']['blocks']]
            logging.debug(parsed_blocks)
            self.wallet.refresh_progressed.emit(self.latest_block, current_block)

            for block_number in parsed_blocks:
                self._parse_block(community, block_number, received_list)
                self.wallet.refresh_progressed.emit(current_block - block_number,
                                                     current_block - self.latest_block)

            if current_block > self.latest_block:
                self.available_sources = self.wallet.sources(community)
                self.latest_block = current_block

            for transfer in awaiting:
                transfer.check_refused(current_block)

        except NoPeerAvailable:
            return


class Wallet(QObject):
    '''
    A wallet is used to manage money with a unique key.
    '''

    inner_data_changed = pyqtSignal(int)
    refresh_progressed = pyqtSignal(int, int)

    def __init__(self, walletid, pubkey, name):
        '''
        Constructor of a wallet object

        :param int walletid: The wallet number, unique between all wallets
        :param str pubkey: The wallet pubkey
        :param str name: The wallet name
        '''
        super().__init__()
        self.coins = []
        self.walletid = walletid
        self.pubkey = pubkey
        self.name = name
        self.caches = {}

    @classmethod
    def create(cls, walletid, salt, password, name):
        '''
        Factory method to create a new wallet

        :param int walletid: The wallet number, unique between all wallets
        :param str salt: The account salt
        :param str password: The account password
        :param str name: The account name
        '''
        if walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, walletid), password)
        return cls(walletid, key.pubkey, name)

    @classmethod
    def load(cls, json_data):
        '''
        Factory method to load a saved wallet.

        :param dict json_data: The wallet as a dict in json format
        '''
        walletid = json_data['walletid']
        pubkey = json_data['pubkey']
        name = json_data['name']
        return cls(walletid, pubkey, name)

    def load_caches(self, json_data):
        '''
        Load this wallet caches.
        Each cache correspond to one different community.

        :param dict json_data: The caches as a dict in json format
        '''
        for currency in json_data:
            if currency != 'version':
                self.caches[currency] = Cache(self)
                self.caches[currency].load_from_json(json_data[currency])

    def jsonify_caches(self):
        '''
        Get this wallet caches as json.

        :return: The wallet caches as a dict in json format
        '''
        data = {}
        for currency in self.caches:
            data[currency] = self.caches[currency].jsonify()
        return data

    def init_cache(self, community):
        '''
        Init the cache of this wallet for the specified community.

        :param community: The community to refresh its cache
        '''
        if community.currency not in self.caches:
            self.caches[community.currency] = Cache(self)

    def refresh_cache(self, community, received_list):
        '''
        Refresh the cache of this wallet for the specified community.

        :param community: The community to refresh its cache
        '''
        self.caches[community.currency].refresh(community, received_list)

    def check_password(self, salt, password):
        '''
        Check if wallet password is ok.

        :param salt: The account salt
        :param password: The given password
        :return: True if (salt, password) generates the good public key
        .. warning:: Generates a new temporary SigningKey from salt and password
        '''
        key = None
        if self.walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password)
        return (key.pubkey == self.pubkey)

    def relative_value(self, community):
        '''
        Get wallet value relative to last generated UD

        :param community: The community to get value
        :return: The wallet relative value
        '''
        value = self.value(community)
        ud = community.dividend
        relative_value = value / float(ud)
        return relative_value

    def value(self, community):
        '''
        Get wallet absolute value

        :param community: The community to get value
        :return: The wallet absolute value
        '''
        value = 0
        for s in self.sources(community):
            value += s.amount
        return value

    def tx_inputs(self, amount, community):
        '''
        Get inputs to generate a transaction with a given amount of money

        :param int amount: The amount target value
        :param community: The community target of the transaction

        :return: The list of inputs to use in the transaction document
        '''
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
        '''
        Get outputs to generate a transaction with a given amount of money

        :param str pubkey: The target pubkey of the transaction
        :param int amount: The amount to send
        :param list inputs: The inputs used to send the given amount of money

        :return: The list of outputs to use in the transaction document
        '''
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
        '''
        Send money to a given recipient in a specified community

        :param str salt: The account salt
        :param str password: The account password
        :param community: The community target of the transfer
        :param str recipient: The pubkey of the recipient
        :param int amount: The amount of money to transfer
        :param str message: The message to send with the transfer
        '''
        time = community.get_block().mediantime
        block_number = community.current_blockid()['number']
        block = community.request(bma.blockchain.Block,
                                  req_args={'number': block_number})
        txid = len(block['transactions'])
        key = None
        logging.debug("Key : {0} : {1}".format(salt, password))
        if self.walletid == 0:
            key = SigningKey(salt, password)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))

        try:
            issuer_uid = Person.lookup(key.pubkey, community).uid
        except PersonNotFoundError:
            issuer_uid = ""

        try:
            receiver_uid = Person.lookup(recipient, community).uid
        except PersonNotFoundError:
            receiver_uid = ""

        metadata = {'block': block_number,
                    'time': time,
                    'amount': amount,
                    'issuer': key.pubkey,
                    'issuer_uid': issuer_uid,
                    'receiver': recipient,
                    'receiver_uid': receiver_uid,
                    'comment': message,
                    'txid': txid
                    }
        transfer = Transfer.initiate(metadata)

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
        '''
        Get available sources in a given community

        :param cutecoin.core.community.Community community: The community where we want available sources
        :return: List of InputSource ucoinpy objects
        '''
        data = community.bma_access.get(self, qtbma.tx.Sources,
                                 req_args={'pubkey': self.pubkey})
        tx = []
        for s in data['sources']:
            tx.append(InputSource.from_bma(s))
        return tx

    def transfers(self, community):
        '''
        Get all transfers objects of this wallet

        :param community: The community we want to get the executed transfers
        :return: A list of Transfer objects
        '''
        return self.caches[community.currency].transfers

    def jsonify(self):
        '''
        Get the wallet as json format.

        :return: The wallet as a dict in json format.
        '''
        return {'walletid': self.walletid,
                'pubkey': self.pubkey,
                'name': self.name}
