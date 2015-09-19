import asyncio
import logging
import hashlib
from .transfer import Transfer
from ucoinpy.documents.transaction import InputSource, OutputSource
from ucoinpy.documents.block import Block
from ..tools.exceptions import LookupFailureError, NoPeerAvailable
from ucoinpy.api import  bma


class TxHistory():
    def __init__(self, app, wallet):
        self._latest_block = 0
        self.wallet = wallet
        self.app = app
        self._stop_coroutines = False

        self._transfers = []
        self.available_sources = []
        self._dividends = []

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
            self._transfers.append(Transfer.load(s))

        for s in data['sources']:
            self.available_sources.append(InputSource.from_inline(s['inline']))

        for d in data['dividends']:
            self._dividends.append(d)

        self.latest_block = data['latest_block']

    def jsonify(self):
        data_transfer = []
        for s in self.transfers:
            data_transfer.append(s.jsonify())

        data_sources = []
        for s in self.available_sources:
            s.index = 0
            data_sources.append({'inline': "{0}\n".format(s.inline())})

        data_dividends = []
        for d in self._dividends:
            data_dividends.append(d)

        return {'latest_block': self.latest_block,
                'transfers': data_transfer,
                'sources': data_sources,
                'dividends': data_dividends}

    @property
    def transfers(self):
        return [t for t in self._transfers if t.state != Transfer.DROPPED]

    @property
    def dividends(self):
        return self._dividends.copy()

    def stop_coroutines(self):
        self._stop_coroutines = True

    @staticmethod
    @asyncio.coroutine
    def _validation_state(community, block_number, current_block):
        members_pubkeys = yield from community.members_pubkeys()
        if block_number + community.network.fork_window(members_pubkeys) <= current_block["number"]:
            state = Transfer.VALIDATED
        else:
            state = Transfer.VALIDATING
        return state

    @asyncio.coroutine
    def _parse_transaction(self, community, tx, block_number,
                           mediantime, received_list,
                           current_block, txid):
        """
        Parse a transaction
        :param cutecoin.core.Community community: The community
        :param ucoinpy.documents.Transaction tx: The tx json data
        :param int block_number: The block number were we found the tx
        :param int mediantime: Median time on the network
        :param list received_list: The list of received transactions
        :param int current_block: The current block of the network
        :param int txid: The latest txid
        :return: the found transaction
        """
        receivers = [o.pubkey for o in tx.outputs
                     if o.pubkey != tx.issuers[0]]

        state = yield from TxHistory._validation_state(community, block_number, current_block)

        if len(receivers) == 0:
            receivers = [tx.issuers[0]]

        try:
            issuer = yield from self.wallet._identities_registry.future_find(tx.issuers[0], community)
            issuer_uid = issuer.uid
        except LookupFailureError:
            issuer_uid = ""

        try:
            receiver = yield from self.wallet._identities_registry.future_find(receivers[0], community)
            receiver_uid = receiver.uid
        except LookupFailureError:
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
        awaiting = [t for t in self._transfers
                    if t.state in (Transfer.AWAITING, Transfer.VALIDATING)]

        # We check if the transaction correspond to one we sent
        # but not from this cutecoin Instance
        tx_hash = hashlib.sha1(tx.signed_raw().encode("ascii")).hexdigest().upper()
        if tx_hash not in [t.hash for t in awaiting]:
            # If the wallet pubkey is in the issuers we sent this transaction
            if in_issuers:
                outputs = [o for o in tx.outputs
                           if o.pubkey != self.wallet.pubkey]
                amount = 0
                for o in outputs:
                    amount += o.amount
                metadata['amount'] = amount
                transfer = Transfer.create_from_blockchain(tx_hash,
                                                           state,
                                                     metadata.copy())
                return transfer
            # If we are not in the issuers,
            # maybe it we are in the recipients of this transaction
            elif in_outputs:
                outputs = [o for o in tx.outputs
                           if o.pubkey == self.wallet.pubkey]
                amount = 0
                for o in outputs:
                    amount += o.amount
                metadata['amount'] = amount

                if tx_hash not in [t.hash for t in awaiting]:
                    transfer = Transfer.create_from_blockchain(tx_hash,
                                                               state,
                                                         metadata.copy())
                    received_list.append(transfer)
                    return transfer
        else:
            transfer = [t for t in awaiting if t.hash == tx_hash][0]

            transfer.check_registered(tx_hash, current_block['number'], mediantime,
                                      community.network.fork_window(community.members_pubkeys()))
        return None

    @asyncio.coroutine
    def _parse_block(self, community, block_number, received_list, current_block, txmax):
        """
        Parse a block
        :param cutecoin.core.Community community: The community
        :param int block_number: The block to request
        :param list received_list: The list where we are appending transactions
        :param int current_block: The current block of the network
        :param int txmax: Latest tx id
        :return: The list of transfers sent
        """
        block = None
        block_doc = None
        tries = 0
        while block is None and tries < 3:
            try:
                block = yield from community.bma_access.future_request(bma.blockchain.Block,
                                      req_args={'number': block_number})
                signed_raw = "{0}{1}\n".format(block['raw'],
                                           block['signature'])
                transfers = []
                try:
                    block_doc = Block.from_signed_raw(signed_raw)
                except TypeError:
                    logging.debug("Error in {0}".format(block_number))
                    block = None
                    tries += 1
            except ValueError as e:
                if '404' in str(e):
                    block = None
                    tries += 1
        if block_doc:
            for (txid, tx) in enumerate(block_doc.transactions):
                transfer = yield from self._parse_transaction(community, tx, block_number,
                                        block_doc.mediantime, received_list,
                                        current_block, txid+txmax)
                if transfer != None:
                    logging.debug("Transfer amount : {0}".format(transfer.metadata['amount']))
                    transfers.append(transfer)
                else:
                    logging.debug("None transfer")
        else:
            logging.debug("Could not find or parse block {0}".format(block_number))
        return transfers

    @asyncio.coroutine
    def request_dividends(self, community, parsed_block):
        for i in range(0, 6):
            try:
                dividends_data = yield from community.bma_access.future_request(bma.ud.History,
                                                req_args={'pubkey': self.wallet.pubkey})

                dividends = dividends_data['history']['history']
                for d in dividends:
                    if d['block_number'] < parsed_block:
                        dividends.remove(d)
                return dividends
            except ValueError as e:
                if '404' in str(e):
                    pass
        return {}

    @asyncio.coroutine
    def refresh(self, community, received_list):
        """
        Refresh last transactions

        :param cutecoin.core.Community community: The community
        :param list received_list: List of transactions received
        """
        try:
            current_block = yield from community.bma_access.future_request(bma.blockchain.Block,
                                    req_args={'number': community.network.latest_block_number})
            members_pubkeys = yield from community.members_pubkeys()
            # We look for the first block to parse, depending on awaiting and validating transfers and ud...
            blocks = [tx.metadata['block'] for tx in self._transfers
                      if tx.state in (Transfer.AWAITING, Transfer.VALIDATING)] +\
                     [ud['block_number'] for ud in self._dividends
                      if ud['state'] in (Transfer.AWAITING, Transfer.VALIDATING)] +\
                     [max(0, self.latest_block - community.network.fork_window(members_pubkeys))]
            parsed_block = min(set(blocks))
            logging.debug("Refresh from : {0} to {1}".format(self.latest_block, current_block['number']))
            dividends = yield from self.request_dividends(community, parsed_block)
            with_tx_data = yield from community.bma_access.future_request(bma.blockchain.TX)
            blocks_with_tx = with_tx_data['result']['blocks']
            new_transfers = []
            new_dividends = []
            # Lets look if transactions took too long to be validated
            awaiting = [t for t in self._transfers
                        if t.state == Transfer.AWAITING]
            while parsed_block <= current_block['number']:
                udid = 0
                for d in [ud for ud in dividends if ud['block_number'] == parsed_block]:
                    state = yield from TxHistory._validation_state(community, d['block_number'], current_block)

                    if d['block_number'] not in [ud['block_number'] for ud in self._dividends]:
                        d['id'] = udid
                        d['state'] = state
                        new_dividends.append(d)
                        udid += 1
                    else:
                        known_dividend = [ud for ud in self._dividends
                                          if ud['block_number'] == d['block_number']][0]
                        known_dividend['state'] = state

                # We parse only blocks with transactions
                if parsed_block in blocks_with_tx:
                    transfers = yield from self._parse_block(community, parsed_block,
                                                             received_list, current_block,
                                                             udid + len(new_transfers))
                    new_transfers += transfers

                self.wallet.refresh_progressed.emit(parsed_block, current_block['number'], self.wallet.pubkey)
                parsed_block += 1

            if current_block['number'] > self.latest_block:
                self.available_sources = yield from self.wallet.sources(community)
                if self._stop_coroutines:
                    return
                self.latest_block = current_block['number']

            parameters = yield from community.parameters()
            for transfer in awaiting:
                transfer.check_refused(current_block['medianTime'],
                                       parameters['avgGenTime'],
                                       parameters['medianTimeBlocks'])
        except NoPeerAvailable as e:
            logging.debug(str(e))
            self.wallet.refresh_finished.emit([])
            return

        self._transfers = self._transfers + new_transfers
        self._dividends = self._dividends + new_dividends

        self.wallet.refresh_finished.emit(received_list)
