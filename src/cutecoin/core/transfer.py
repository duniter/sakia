'''
Created on 31 janv. 2015

@author: inso
'''
import logging
from ucoinpy.api import bma
from ucoinpy.documents.transaction import Transaction


class Transfer(object):
    '''
    A transaction
    '''
    TO_SEND = 0
    AWAITING = 1
    VALIDATED = 2
    REFUSED = 3
    SENT = 4
    DROPPED = 5

    def __init__(self, txdoc, state, metadata):
        '''
        Constructor
        '''
        assert('receiver' in metadata)
        assert('block' in metadata)
        assert('time' in metadata)
        assert('issuer' in metadata)
        assert('amount' in metadata)
        assert('comment' in metadata)

        self.txdoc = txdoc
        self.state = state
        self._metadata = metadata

    @classmethod
    def initiate(cls, metadata):
        return cls(None, Transfer.TO_SEND, metadata)

    @classmethod
    def create_validated(cls, txdoc, metadata):
        logging.debug("VALIDATED : {0}".format(metadata))
        return cls(txdoc, Transfer.VALIDATED, metadata)

    @property
    def metadata(self):
        return self._metadata

    @classmethod
    def load(cls, data):
        if data['state'] is Transfer.TO_SEND:
            txdoc = None
        else:
            txdoc = Transaction.from_signed_raw(data['txdoc'])
        return cls(txdoc, data['state'], data['metadata'])

    def jsonify(self):
        if self.txdoc:
            txraw = self.txdoc.signed_raw()
        else:
            txraw = None
        return {'txdoc': txraw,
                'state': self.state,
                'metadata': self._metadata}

    def send(self, txdoc, community):
        try:
            self.txdoc = txdoc
            community.broadcast(bma.tx.Process,
                        post_args={'transaction': self.txdoc.signed_raw()})
            self.state = Transfer.AWAITING
        except ValueError as e:
            if '400' in str(e):
                self.state = Transfer.REFUSED
            raise
        finally:
            self._metadata['block'] = community.current_blockid()['number']
            self._metadata['time'] = community.get_block().mediantime

    def check_registered(self, tx, block, time):
        logging.debug("REGISTERED : BEFORE : {0}".format(self._metadata))
        if tx.signed_raw() == self.txdoc.signed_raw():
            self.state = Transfer.VALIDATED
            self._metadata['block'] = block
            self._metadata['time'] = time
        logging.debug("REGISTERED : AFTER : {0}".format(self._metadata))

    def check_refused(self, block):
        logging.debug("REFUSED : BEFORE : {0}".format(self._metadata))
        if block > self._metadata['block'] + 15:
            self.state = Transfer.REFUSED
        logging.debug("REFUSED : AFTER : {0}".format(self._metadata))

    def drop(self):
        self.state = Transfer.DROPPED


class Received(Transfer):
    def __init__(self, txdoc, metadata):
        '''
        Constructor
        '''
        super().__init__(txdoc, Transfer.VALIDATED, metadata)

    @classmethod
    def load(cls, data):
        txdoc = Transaction.from_signed_raw(data['txdoc'])
        return cls(txdoc, data['metadata'])
