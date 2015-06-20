'''
Created on 31 janv. 2015

@author: inso
'''
import logging
from ucoinpy.documents.transaction import Transaction
from .net.api import bma as qtbma
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtNetwork import QNetworkReply
import hashlib

class Transfer(QObject):
    '''
    A transfer is the lifecycle of a transaction.
    TO_SEND means the transaction wasn't sent yet
    AWAITING means the transaction is waiting for a blockchain validation
    VALIDATED means the transaction was registered in the blockchain
    REFUSED means the transaction took too long to be registered in the blockchain,
    therefore it is considered as refused
    DROPPED means the transaction was canceled locally. It can still be validated
    in the blockchain if it was sent, if the guy is unlucky ;)
    '''
    TO_SEND = 0
    AWAITING = 1
    VALIDATED = 2
    REFUSED = 3
    DROPPED = 5

    transfer_broadcasted = pyqtSignal()
    broadcast_error = pyqtSignal(str, str)

    def __init__(self, hash, state, metadata):
        '''
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
        '''
        assert('receiver' in metadata)
        assert('block' in metadata)
        assert('time' in metadata)
        assert('issuer' in metadata)
        assert('amount' in metadata)
        assert('comment' in metadata)
        assert('issuer_uid' in metadata)
        assert('receiver_uid' in metadata)
        assert('txid' in metadata)

        self.hash = hash
        self.state = state
        self._metadata = metadata

    @classmethod
    def initiate(cls, metadata):
        '''
        Create a new transfer in a "TO_SEND" state.
        '''
        return cls(None, Transfer.TO_SEND, metadata)

    @classmethod
    def create_validated(cls, hash, metadata):
        '''
        Create a new transfer in a "VALIDATED" state.
        '''
        return cls(hash, Transfer.VALIDATED, metadata)

    @classmethod
    def load(cls, data):
        '''
        Create a new transfer from a dict in json format.
        '''
        return cls(data['hash'], data['state'], data['metadata'])

    @property
    def metadata(self):
        '''
        :return: this transfer metadata
        '''
        return self._metadata

    def jsonify(self):
        '''
        :return: The transfer as a dict in json format
        '''
        return {'hash': self.hash,
                'state': self.state,
                'metadata': self._metadata}

    def send(self, txdoc, community):
        '''
        Send a transaction and update the transfer state to AWAITING if accepted.
        If the transaction was refused (return code != 200), state becomes REFUSED
        The txdoc is saved as the transfer txdoc.

        :param txdoc: A transaction ucoinpy object
        :param community: The community target of the transaction
        '''
        replies = community.bma_access.broadcast(qtbma.tx.Process,
                    post_args={'transaction': self.txdoc.signed_raw()})
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_transfers_reply(replies, reply))

        self.state = Transfer.AWAITING
        self.hash = hashlib.sha1(txdoc.signed_raw().encode("ascii")).hexdigest().upper()
        self._metadata['block'] = community.current_blockid()['number']
        self._metadata['time'] = community.get_block().mediantime

    def __handle_transfers_reply(self, replies, reply):
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            self.transfer_broadcasted.emit()
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    def check_registered(self, tx, block, time):
        '''
        Check if the transfer was registered in a block.
        Update the transfer state to VALIDATED if it was registered.

        :param tx: A transaction ucoinpy object found in the block
        :param int block: The block number checked
        :param int time: The time of the block
        '''
        if tx.signed_raw() == self.txdoc.signed_raw():
            self.state = Transfer.VALIDATED
            self._metadata['block'] = block
            self._metadata['time'] = time

    def check_refused(self, block):
        '''
        Check if the transfer was refused
        If more than 15 blocks were mined since the transaction
        transfer, it is considered as refused.

        :param int block: The current block number
        '''
        if block > self._metadata['block'] + 15:
            self.state = Transfer.REFUSED

    def drop(self):
        '''
        Cancel the transfer locally.
        The transfer state becomes "DROPPED".
        '''
        self.state = Transfer.DROPPED


class Received(Transfer):
    def __init__(self, hash, metadata):
        '''
        A transfer were the receiver is the local user.

        :param txdoc: The transaction document of the received transfer
        :param metadata: The metadata of the transfer
        '''
        super().__init__(hash, Transfer.VALIDATED, metadata)

    @classmethod
    def load(cls, data):
        '''
        Create a transfer from a dict in json format.

        :param data: The transfer as a dict in json format
        '''
        return cls(data['hash'], data['metadata'])
