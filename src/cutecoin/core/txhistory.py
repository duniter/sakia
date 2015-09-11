import asyncio
import logging
from .transfer import Transfer
from ucoinpy.documents.transaction import InputSource, OutputSource
from ..tools.exceptions import LookupFailureError
from .net.api import bma as qtbma


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
    def _validation_state(community, block_number, current_block):
        if block_number + community.network.fork_window(community.members_pubkeys()) + 1 < current_block["number"]:
            state = Transfer.VALIDATED
        else:
            state = Transfer.VALIDATING
        return state

    @asyncio.coroutine
    def _parse_transaction(self, community, txdata, received_list, txid, current_block):
        tx_outputs = [OutputSource.from_inline(o) for o in txdata['outputs']]
        receivers = [o.pubkey for o in tx_outputs
                     if o.pubkey != txdata['issuers'][0]]

        block_number = txdata['block_number']

        mediantime = txdata['time']
        state = TxHistory._validation_state(community, block_number, current_block)

        if len(receivers) == 0:
            receivers = [txdata['issuers'][0]]

        try:
            issuer = yield from self.wallet._identities_registry.future_find(txdata['issuers'][0], community)
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
                    'comment': txdata['comment'],
                    'issuer': txdata['issuers'][0],
                    'issuer_uid': issuer_uid,
                    'receiver': receivers[0],
                    'receiver_uid': receiver_uid,
                    'txid': txid}

        in_issuers = len([i for i in txdata['issuers']
                     if i == self.wallet.pubkey]) > 0
        in_outputs = len([o for o in tx_outputs
                       if o.pubkey == self.wallet.pubkey]) > 0
        awaiting = [t for t in self._transfers
                    if t.state in (Transfer.AWAITING, Transfer.VALIDATING)]

        # We check if the transaction correspond to one we sent
        # but not from this cutecoin Instance
        if txdata['hash'] not in [t.hash for t in awaiting]:
            # If the wallet pubkey is in the issuers we sent this transaction
            if in_issuers:
                outputs = [o for o in tx_outputs
                           if o.pubkey != self.wallet.pubkey]
                amount = 0
                for o in outputs:
                    amount += o.amount
                metadata['amount'] = amount
                transfer = Transfer.create_from_blockchain(txdata['hash'],
                                                           state,
                                                     metadata.copy())
                return transfer
            # If we are not in the issuers,
            # maybe it we are in the recipients of this transaction
            elif in_outputs:
                outputs = [o for o in tx_outputs
                           if o.pubkey == self.wallet.pubkey]
                amount = 0
                for o in outputs:
                    amount += o.amount
                metadata['amount'] = amount

                if txdata['hash'] not in [t.hash for t in awaiting]:
                    transfer = Transfer.create_from_blockchain(txdata['hash'],
                                                               state,
                                                         metadata.copy())
                    received_list.append(transfer)
                    return transfer
        else:
            transfer = [t for t in awaiting if t.hash == txdata['hash']][0]
            transfer.check_registered(txdata['hash'], current_block['number'], mediantime,
                                      community.network.fork_window(community.members_pubkeys()) + 1)
        return None

    @asyncio.coroutine
    def refresh(self, community, received_list):
        """
        Refresh last transactions

        :param cutecoin.core.Community community: The community
        :param list received_list: List of transactions received
        """
        current_block = yield from community.bma_access.future_request(qtbma.blockchain.Block,
                                req_args={'number': community.network.latest_block_number})

        # We look for the first block to parse, depending on awaiting and validating transfers and ud...
        blocks = [tx.metadata['block'] for tx in self._transfers
                  if tx.state in (Transfer.AWAITING, Transfer.VALIDATING)] +\
                 [ud['block_number'] for ud in self._dividends
                  if ud['state'] in (Transfer.AWAITING, Transfer.VALIDATING)] +\
                 [max(0, self.latest_block - community.network.fork_window(community.members_pubkeys()))]
        parsed_block = min(set(blocks))
        logging.debug("Refresh from : {0} to {1}".format(self.latest_block, current_block['number']))
        dividends_data = qtbma.ud.History.null_value
        for i in range(0, 6):
            if dividends_data == qtbma.ud.History.null_value:
                if i == 5:
                    return
                dividends_data = yield from community.bma_access.future_request(qtbma.ud.History,
                                                req_args={'pubkey': self.wallet.pubkey})

        dividends = dividends_data['history']['history']
        for d in dividends:
            if d['block_number'] < parsed_block:
                dividends.remove(d)

        new_transfers = []
        new_dividends = []
        # Lets look if transactions took too long to be validated
        awaiting = [t for t in self._transfers
                    if t.state == Transfer.AWAITING]
        while parsed_block < current_block['number']:
            tx_history = qtbma.tx.history.Blocks.null_value
            for i in range(0, 6):
                if tx_history == qtbma.tx.history.Blocks.null_value:
                    if i == 5:
                        return

                    tx_history = yield from community.bma_access.future_request(qtbma.tx.history.Blocks,
                                                          req_args={'pubkey': self.wallet.pubkey,
                                                                 'from_':str(parsed_block),
                                                                 'to_': str(parsed_block + 99)})
            if self._stop_coroutines:
                return

            udid = 0
            for d in [ud for ud in dividends if ud['block_number'] in range(parsed_block, parsed_block+100)]:
                state = TxHistory._validation_state(community, d['block_number'], current_block)

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
            transactions = tx_history['history']['received'] + tx_history['history']['sent']
            for (txid, txdata) in enumerate(transactions):
                if self._stop_coroutines:
                    return
                if len(txdata['issuers']) == 0:
                    logging.debug("Error with : {0}, from {1} to {2}".format(self.wallet.pubkey,
                                                                             parsed_block,
                                                                             current_block['number']))
                else:
                    transfer = yield from self._parse_transaction(community, txdata, received_list,
                                                                  udid + txid, current_block)
                    if transfer:
                        new_transfers.append(transfer)

            self.wallet.refresh_progressed.emit(parsed_block, current_block['number'], self.wallet.pubkey)
            parsed_block += 100

        if current_block['number'] > self.latest_block:
            self.available_sources = yield from self.wallet.future_sources(community)
            if self._stop_coroutines:
                return
            self.latest_block = current_block['number']

        for transfer in awaiting:
            transfer.check_refused(current_block['medianTime'],
                                   community.parameters['avgGenTime'],
                                   community.parameters['medianTimeBlocks'])

        self._transfers = self._transfers + new_transfers
        self._dividends = self._dividends + new_dividends

        self.wallet.refresh_finished.emit(received_list)
