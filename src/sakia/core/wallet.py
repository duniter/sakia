"""
Created on 1 févr. 2014

@author: inso
"""

from duniterpy.documents.transaction import InputSource, OutputSource, Unlock, SIGParameter, Transaction, reduce_base
from duniterpy.grammars import output
from duniterpy.key import SigningKey

from duniterpy.api import bma
from duniterpy.api.bma import PROTOCOL_VERSION
from ..tools.exceptions import NotEnoughMoneyError, NoPeerAvailable, LookupFailureError
from .transfer import Transfer
from .txhistory import TxHistory
from .. import __version__

from pkg_resources import parse_version
from PyQt5.QtCore import QObject, pyqtSignal

import logging
import asyncio


class Wallet(QObject):
    """
    A wallet is used to manage money with a unique key.
    """
    refresh_progressed = pyqtSignal(int, int, str)
    refresh_finished = pyqtSignal(list)

    def __init__(self, walletid, pubkey, name, identities_registry):
        """
        Constructor of a wallet object

        :param int walletid: The wallet number, unique between all wallets
        :param str pubkey: The wallet pubkey
        :param str name: The wallet name
        """
        super().__init__()
        self.coins = []
        self.walletid = walletid
        self.pubkey = pubkey
        self.name = name
        self._identities_registry = identities_registry
        self.caches = {}

    @classmethod
    def create(cls, walletid, salt, password, scrypt_params, name, identities_registry):
        """
        Factory method to create a new wallet

        :param int walletid: The wallet number, unique between all wallets
        :param str salt: The account salt
        :param str password: The account password
        :param duniterpy.key.ScryptParams scrypt_params: the scrypt params
        :param str name: The account name
        """
        if walletid == 0:
            key = SigningKey(salt, password, scrypt_params)
        else:
            key = SigningKey(b"{0}{1}".format(salt, walletid), password, scrypt_params)
        return cls(walletid, key.pubkey, name, identities_registry)

    @classmethod
    def load(cls, json_data, identities_registry):
        """
        Factory method to load a saved wallet.

        :param dict json_data: The wallet as a dict in json format
        """
        walletid = json_data['walletid']
        pubkey = json_data['pubkey']
        name = json_data['name']
        return cls(walletid, pubkey, name, identities_registry)

    def load_caches(self, app, json_data):
        """
        Load this wallet caches.
        Each cache correspond to one different community.

        :param dict json_data: The caches as a dict in json format
        """
        version = parse_version(json_data['version'])
        for currency in json_data:
            if currency != 'version':
                self.caches[currency] = TxHistory(app, self)
                if version >= parse_version("0.20.dev0"):
                    self.caches[currency].load_from_json(json_data[currency], version)

    def jsonify_caches(self):
        """
        Get this wallet caches as json.

        :return: The wallet caches as a dict in json format
        """
        data = {}
        for currency in self.caches:
            data[currency] = self.caches[currency].jsonify()
        return data

    def init_cache(self, app, community):
        """
        Init the cache of this wallet for the specified community.

        :param community: The community to refresh its cache
        """
        if community.currency not in self.caches:
            self.caches[community.currency] = TxHistory(app, self)

    def refresh_transactions(self, community, received_list):
        """
        Refresh the cache of this wallet for the specified community.

        :param community: The community to refresh its cache
        """
        logging.debug("Refresh transactions for {0}".format(self.pubkey))
        asyncio.ensure_future(self.caches[community.currency].refresh(community, received_list))

    def rollback_transactions(self, community, received_list):
        """
        Rollback the transactions of this wallet for the specified community.

        :param community: The community to refresh its cache
        """
        logging.debug("Refresh transactions for {0}".format(self.pubkey))
        asyncio.ensure_future(self.caches[community.currency].rollback(community, received_list))

    async def relative_value(self, community):
        """
        Get wallet value relative to last generated UD

        :param community: The community to get value
        :return: The wallet relative value
        """
        value = await self.value(community)
        ud = community.dividend
        relative_value = value / float(ud)
        return relative_value

    async def value(self, community):
        """
        Get wallet absolute value

        :param community: The community to get value
        :return: The wallet absolute value
        """
        value = 0
        sources = await self.sources(community)
        for s in sources:
            value += s['amount'] * pow(10, s['base'])
        return value

    def tx_sources(self, amount, community):
        """
        Get inputs to generate a transaction with a given amount of money

        :param int amount: The amount target value
        :param community: The community target of the transaction

        :return: The list of inputs to use in the transaction document
        """

        # such a dirty algorithmm
        # everything should be done again from scratch
        # in future versions

        def current_value(inputs, overhs):
            i = 0
            for s in inputs:
                i += s['amount'] * (10**s['base'])
            for o in overhs:
                i -= o[0] * (10**o[1])
            return i

        amount, amount_base = reduce_base(amount, 0)
        cache = self.caches[community.currency]
        if cache.available_sources:
            current_base = max([src['base'] for src in cache.available_sources])
            value = 0
            sources = []
            outputs = []
            overheads = []
            buf_sources = list(cache.available_sources)
            while current_base >= 0:
                for s in [src for src in cache.available_sources if src['base'] == current_base]:
                    test_sources = sources + [s]
                    val = current_value(test_sources, overheads)
                    # if we have to compute an overhead
                    if current_value(test_sources, overheads) > amount * (10**amount_base):
                        overhead = current_value(test_sources, overheads) - int(amount) * (10**amount_base)
                        # we round the overhead in the current base
                        # exemple : 12 in base 1 -> 1*10^1
                        overhead = int(round(float(overhead) / (10**current_base)))
                        source_value = s['amount'] * (10**s['base'])
                        out = int((source_value - (overhead * (10**current_base)))/(10**current_base))
                        if out * (10**current_base) <= amount * (10**amount_base):
                            sources.append(s)
                            buf_sources.remove(s)
                            overheads.append((overhead, current_base))
                            outputs.append((out, current_base))
                    # else just add the output
                    else:
                        sources.append(s)
                        buf_sources.remove(s)
                        outputs.append((s['amount'] , s['base']))
                    if current_value(sources, overheads) == amount * (10 ** amount_base):
                        return sources, outputs, overheads, buf_sources

                current_base -= 1

        raise NotEnoughMoneyError(value, community.currency,
                                  len(sources), amount * pow(10, amount_base))

    def tx_inputs(self, sources):
        """
        Get inputs to generate a transaction with a given amount of money

        :param list sources: The sources used to send the given amount of money

        :return: The list of inputs to use in the transaction document
        """
        inputs = []
        for s in sources:
            inputs.append(InputSource(s['amount'], s['base'], s['type'], s['identifier'], s['noffset']))
        return inputs

    def tx_unlocks(self, sources):
        """
        Get unlocks to generate a transaction with a given amount of money

        :param list sources: The sources used to send the given amount of money

        :return: The list of unlocks to use in the transaction document
        """
        unlocks = []
        for i, s in enumerate(sources):
            unlocks.append(Unlock(i, [SIGParameter(0)]))
        return unlocks

    def tx_outputs(self, pubkey, outputs, overheads):
        """
        Get outputs to generate a transaction with a given amount of money

        :param str pubkey: The target pubkey of the transaction
        :param list outputs: The amount to send
        :param list inputs: The inputs used to send the given amount of money
        :param list overheads: The overheads used to send the given amount of money

        :return: The list of outputs to use in the transaction document
        """
        total = []
        outputs_bases = set(o[1] for o in outputs)
        for base in outputs_bases:
            output_sum = 0
            for o in outputs:
                if o[1] == base:
                    output_sum += o[0]
            total.append(OutputSource(output_sum, base, output.Condition.token(output.SIG.token(pubkey))))

        overheads_bases = set(o[1] for o in overheads)
        for base in overheads_bases:
            overheads_sum = 0
            for o in overheads:
                if o[1] == base:
                    overheads_sum += o[0]
            total.append(OutputSource(overheads_sum, base, output.Condition.token(output.SIG.token(self.pubkey))))

        return total

    def prepare_tx(self, pubkey, blockstamp, amount, message, community):
        """
        Prepare a simple Transaction document
        :param str pubkey: the target of the transaction
        :param duniterpy.documents.BlockUID blockstamp: the blockstamp
        :param int amount: the amount sent to the receiver
        :param Community community: the target community
        :return: the transaction document
        :rtype: duniterpy.documents.Transaction
        """
        result = self.tx_sources(int(amount), community)
        sources = result[0]
        computed_outputs = result[1]
        overheads = result[2]
        self.caches[community.currency].available_sources = result[3][1:]
        logging.debug("Inputs : {0}".format(sources))

        inputs = self.tx_inputs(sources)
        unlocks = self.tx_unlocks(sources)
        outputs = self.tx_outputs(pubkey, computed_outputs, overheads)
        logging.debug("Outputs : {0}".format(outputs))
        tx = Transaction(3, community.currency, blockstamp, 0,
                         [self.pubkey], inputs, unlocks,
                         outputs, message, None)
        return tx

    async def send_money(self, salt, password, scrypt_params, community,
                   recipient, amount, message):
        """
        Send money to a given recipient in a specified community

        :param str salt: The account salt
        :param str password: The account password
        :param community: The community target of the transfer
        :param str recipient: The pubkey of the recipient
        :param int amount: The amount of money to transfer
        :param str message: The message to send with the transfer
        """
        try:
            blockUID = community.network.current_blockUID
            block = await community.bma_access.future_request(bma.blockchain.Block,
                                      req_args={'number': blockUID.number})
        except ValueError as e:
            if '404' in str(e):
                return False, "Could not send transfer with null blockchain"

        time = block['medianTime']
        txid = len(block['transactions'])
        if self.walletid == 0:
            key = SigningKey(salt, password, scrypt_params)
        else:
            key = SigningKey("{0}{1}".format(salt, self.walletid), password, scrypt_params)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))

        try:
            issuer = await self._identities_registry.future_find(key.pubkey, community)
            issuer_uid = issuer.uid
        except LookupFailureError as e:
            issuer_uid = ""

        try:
            receiver = await self._identities_registry.future_find(recipient, community)
            receiver_uid = receiver.uid
        except LookupFailureError as e:
            receiver_uid = ""

        metadata = {'block': None,
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
        try:
            tx = self.prepare_tx(recipient, blockUID, amount, message, community)
            logging.debug("TX : {0}".format(tx.raw()))

            tx.sign([key])
            logging.debug("Transaction : [{0}]".format(tx.signed_raw()))
            return await transfer.send(tx, community)
        except NotEnoughMoneyError as e:
            return (False, str(e))

    async def sources(self, community):
        """
        Get available sources in a given community

        :param sakia.core.community.Community community: The community where we want available sources
        :return: List of bma sources
        """
        sources = []
        try:
            data = await community.bma_access.future_request(bma.tx.Sources,
                                     req_args={'pubkey': self.pubkey})
            return data['sources'].copy()
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return sources

    def transfers(self, community):
        """
        Get all transfers objects of this wallet

        :param community: The community we want to get the executed transfers
        :return: A list of Transfer objects
        """
        if community.currency in self.caches:
            return self.caches[community.currency].transfers
        else:
            return []

    def dividends(self, community):
        """
        Get all the dividends received by this wallet

        :param community:  The community we want to get received dividends
        :return: Result of udhistory request
        """
        if community.currency in self.caches:
            return self.caches[community.currency].dividends
        else:
            return []

    def stop_coroutines(self, closing=False):
        for c in self.caches.values():
            c.stop_coroutines(closing)

    def jsonify(self):
        """
        Get the wallet as json format.

        :return: The wallet as a dict in json format.
        """
        return {'walletid': self.walletid,
                'pubkey': self.pubkey,
                'name': self.name,
                'version': __version__}
