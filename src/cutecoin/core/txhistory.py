import asyncio
import logging
from .transfer import Transfer, Received
from ucoinpy.documents.transaction import InputSource, OutputSource
from ..tools.exceptions import LookupFailureError
from .net.api import bma as qtbma

class TxHistory():
    def __init__(self, wallet):
        self._latest_block = 0
        self.wallet = wallet
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
            if s['metadata']['issuer'] == self.wallet.pubkey:
                self._transfers.append(Transfer.load(s))
            else:
                self._transfers.append(Received.load(s))

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

    @asyncio.coroutine
    def _parse_transaction(self, community, txdata, received_list, txid):
        tx_outputs = [OutputSource.from_inline(o) for o in txdata['outputs']]
        receivers = [o.pubkey for o in tx_outputs
                     if o.pubkey != txdata['issuers'][0]]

        block_number = txdata['block_number']
        mediantime = txdata['time']
        logging.debug(txdata)

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

        # If the wallet pubkey is in the issuers we sent this transaction
        if in_issuers:
            outputs = [o for o in tx_outputs
                       if o.pubkey != self.wallet.pubkey]
            amount = 0
            for o in outputs:
                amount += o.amount
            metadata['amount'] = amount

            awaiting = [t for t in self._transfers
                        if t.state == Transfer.AWAITING]
            # We check if the transaction correspond to one we sent
            if txdata['hash'] not in [t['hash'] for t in awaiting]:
                transfer = Transfer.create_validated(txdata['hash'],
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
            received = Received(txdata['hash'], metadata.copy())
            received_list.append(received)
            return received
        return None

    @asyncio.coroutine
    def refresh(self, community, received_list):
        """
        Refresh last transactions

        :param cutecoin.core.Community community: The community
        :param list received_list: List of transactions received
        """
        parsed_block = self.latest_block
        current_block = community.network.latest_block_number
        logging.debug("Refresh from : {0} to {1}".format(self.latest_block, current_block))
        dividends_data = qtbma.ud.History.null_value
        while dividends_data == qtbma.ud.History.null_value:
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
        while parsed_block < current_block:
            tx_history = qtbma.tx.history.Blocks.null_value
            while tx_history == qtbma.tx.history.Blocks.null_value:
                tx_history = yield from community.bma_access.future_request(qtbma.tx.history.Blocks,
                                                          req_args={'pubkey': self.wallet.pubkey,
                                                                 'from_':str(parsed_block),
                                                                 'to_': str(parsed_block + 99)})
            if self._stop_coroutines:
                return

            udid = 0
            for d in dividends:
                if d['block_number'] in range(parsed_block, parsed_block+100):
                    d['id'] = udid
                    new_dividends.append(d)
                    udid += 1

            # We parse only blocks with transactions
            transactions = tx_history['history']['received'] + tx_history['history']['sent']
            for (txid, txdata) in enumerate(transactions):
                if self._stop_coroutines:
                    return
                if len(txdata['issuers']) == 0:
                    logging.debug("Error with : {0}, from {1} to {2}".format(self.wallet.pubkey,
                                                                             parsed_block,
                                                                             current_block))
                else:
                    transfer = yield from self._parse_transaction(community, txdata, received_list, udid + txid)
                    if transfer:
                        new_transfers.append(transfer)

            self.wallet.refresh_progressed.emit(parsed_block, current_block, self.wallet.pubkey)
            parsed_block += 100

        if current_block > self.latest_block:
            self.available_sources = yield from self.wallet.future_sources(community)
            if self._stop_coroutines:
                return
            self.latest_block = current_block

        for transfer in awaiting:
            transfer.check_refused(current_block)

        self._transfers = self._transfers + new_transfers
        self._dividends = self._dividends + new_dividends

        self.wallet.refresh_finished.emit(received_list)
