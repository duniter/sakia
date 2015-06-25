import asyncio
import logging
from .transfer import Transfer, Received
from ucoinpy.documents.transaction import InputSource, OutputSource, Transaction
from ..tools.exceptions import LookupFailureError

class TxHistory():
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

    @asyncio.coroutine
    def _parse_transaction(self, community, txdata, received_list, txid):
        if len(txdata['issuers']) == 0:
            True

        tx_outputs = [OutputSource.from_inline(o) for o in txdata['outputs']]
        receivers = [o.pubkey for o in tx_outputs
                     if o.pubkey != txdata['issuers'][0]]

        block_number = txdata['block_number']
        mediantime = txdata['time']
        logging.debug(txdata)

        if len(receivers) == 0:
            receivers = [txdata['issuers'][0]]

        try:
            issuer = yield from self.wallet._identities_registry.future_lookup(txdata['issuers'][0], community)
            issuer_uid = issuer.uid
        except LookupFailureError:
            issuer_uid = ""

        try:
            receiver = yield from self.wallet._identities_registry.future_lookup(receivers[0], community)
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
                self._transfers.append(transfer)
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
            self._transfers.append(received)
        return True

    @asyncio.coroutine
    def refresh(self, community, received_list):
        """
        Refresh last transactions

        :param cutecoin.core.Community community: The community
        :param list received_list: List of transactions received
        """
        parsed_block = self.latest_block
        block_data = yield from community.blockid()
        current_block = block_data['number']
        logging.debug("Refresh from : {0} to {1}".format(self.latest_block, current_block))

        # Lets look if transactions took too long to be validated
        awaiting = [t for t in self._transfers
                    if t.state == Transfer.AWAITING]
        while parsed_block < current_block:
            tx_history = yield from community.bma_access.future_request(qtbma.tx.history.Blocks,
                                                      req_args={'pubkey': self.wallet.pubkey,
                                                             'from_':str(parsed_block),
                                                             'to_': str(parsed_block + 100)})

            # We parse only blocks with transactions
            transactions = tx_history['history']['received'] + tx_history['history']['sent']
            for (txid, txdata) in enumerate(transactions):
                if len(txdata['issuers']) == 0:
                    logging.debug("Error with : {0}, from {1} to {2}".format(self.wallet.pubkey,
                                                                             parsed_block,
                                                                             current_block))
                else:
                    yield from self._parse_transaction(community, txdata, received_list, txid)
            self.wallet.refresh_progressed.emit(parsed_block, current_block, self.wallet.pubkey)
            parsed_block += 101

        if current_block > self.latest_block:
            self.available_sources = yield from self.wallet.future_sources(community)
            self.latest_block = current_block

        for transfer in awaiting:
            transfer.check_refused(current_block)

        self.wallet.refresh_finished.emit(received_list)
