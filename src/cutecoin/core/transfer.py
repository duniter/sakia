"""
Created on 31 janv. 2015

@author: inso
"""
import logging
import asyncio
from .net.api import bma as qtbma
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtNetwork import QNetworkReply
import hashlib

class Transfer(QObject):
    """
    A transfer is the lifecycle of a transaction.
    TO_SEND means the transaction wasn't sent yet
    AWAITING means the transaction is waiting to reach K blockchain validation
    VALIDATED means the transaction was validated locally and is considered present in the blockchain
    REFUSED means the transaction took too long to be registered in the blockchain,
    therefore it is considered as refused
    DROPPED means the transaction was canceled locally. It can still be validated
    in the blockchain if it was sent, if the guy is unlucky ;)
    """
    TO_SEND = 0
    AWAITING = 1
    VALIDATING = 4
    VALIDATED = 2
    REFUSED = 3
    DROPPED = 5

    transfer_broadcasted = pyqtSignal(str)
    broadcast_error = pyqtSignal(int, str)

    def __init__(self, hash, state, metadata):
        """
        The constructor of a transfer.
        Check for metadata keys which must be present :
        - receiver
        - block
        - time
        - issuer
        - amount
        - comment

        :param txdoc: The Transaction ucoinpy object
        :param state: The state of the Transfer (TO_SEND, AWAITING, VALIDATED, REFUSED or DROPPED)
        :param metadata: The transfer metadata
        """
        assert('receiver' in metadata)
        assert('block' in metadata)
        assert('time' in metadata)
        assert('issuer' in metadata)
        assert('amount' in metadata)
        assert('comment' in metadata)
        assert('issuer_uid' in metadata)
        assert('receiver_uid' in metadata)
        assert('txid' in metadata)
        super().__init__()

        self.hash = hash
        self.state = state
        self._metadata = metadata

    @classmethod
    def initiate(cls, metadata):
        """
        Create a new transfer in a "TO_SEND" state.
        """
        return cls(None, Transfer.TO_SEND, metadata)

    @classmethod
    def create_from_blockchain(cls, hash, state, metadata):
        """
        Create a new transfer sent from another cutecoin instance
        """
        return cls(hash, state, metadata)

    @classmethod
    def load(cls, data):
        """
        Create a new transfer from a dict in json format.
        """
        return cls(data['hash'], data['state'], data['metadata'])

    @property
    def metadata(self):
        """
        :return: this transfer metadata
        """
        return self._metadata

    def jsonify(self):
        """
        :return: The transfer as a dict in json format
        """
        return {'hash': self.hash,
                'state': self.state,
                'metadata': self._metadata}

    @asyncio.coroutine
    def send(self, txdoc, community):
        """
        Send a transaction and update the transfer state to AWAITING if accepted.
        If the transaction was refused (return code != 200), state becomes REFUSED
        The txdoc is saved as the transfer txdoc.

        :param txdoc: A transaction ucoinpy object
        :param community: The community target of the transaction
        """
        replies = community.bma_access.broadcast(qtbma.tx.Process,
                    post_args={'transaction': txdoc.signed_raw()})
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_transfers_reply(replies, reply))

        self.state = Transfer.AWAITING
        self.hash = hashlib.sha1(txdoc.signed_raw().encode("ascii")).hexdigest().upper()
        blockid = yield from community.blockid()
        block = yield from community.bma_access.future_request(qtbma.blockchain.Block,
                                  req_args={'number': blockid['number']})
        if block != qtbma.Blockchain.Block.null_value:
            self._metadata['block'] = blockid['number']
            self._metadata['time'] = block['medianTime']

    def __handle_transfers_reply(self, replies, reply):
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
            self.transfer_broadcasted.emit(self.metadata['receiver_uid'])
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    def check_registered(self, tx, block, time, data_validation):
        """
        Check if the transfer was registered in a block.
        Update the transfer state to VALIDATED if it was registered.

        :param tx: A transaction ucoinpy object found in the block
        :param int block: The block number checked
        :param int time: The time of the block
        """
        if tx.signed_raw() == self.txdoc.signed_raw():
            if self.state == Transfer.AWAITING:
                self.state = Transfer.VALIDATING
                self._metadata['block'] = block
                self._metadata['time'] = time
            elif self.state == Transfer.VALIDATING and \
                    self._metadata['block'] - block > data_validation:
                self.state = Transfer.VALIDATED

    def check_refused(self, time, block_time, mediantime_blocks):
        """
        Check if the transfer was refused
        If more than block_time*15 seconds passed since
        transfer, it is considered as refused.

        :param int block: The current block number
        """
        if time > self._metadata['time'] + block_time*mediantime_blocks*10:
            self.state = Transfer.REFUSED

    def drop(self):
        """
        Cancel the transfer locally.
        The transfer state becomes "DROPPED".
        """
        self.state = Transfer.DROPPED

