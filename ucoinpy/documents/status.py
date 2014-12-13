'''
Created on 2 déc. 2014

@author: inso
'''

from . import Document
from .. import PROTOCOL_VERSION


class Status(Document):
    '''
    Version: VERSION
    Type: Status
    Currency: CURRENCY_NAME
    Status: STATUS
    Block: BLOCK
    From: SENDER
    To: RECIPIENT
    '''

    def __init__(self, version, currency, status, blockid, sender,
                 recipient, signature):
        '''
        Constructor
        '''
        super().__init__(version, currency, [signature])
        self.status = status
        self.blockid = blockid
        self.sender = sender
        self.recipient = recipient

    @classmethod
    def from_raw(cls, raw):
        #TODO : Parsing
        return cls()

    def raw(self):
        return '''
Version: {0}
Type: Status
Currency: {1}
Status: {2}
Block: {3}
From: {4}
To: {5}
{6}
'''.format(self.version, self.currency, self.status,
           self.blockid, self.sender, self.recipient, self.signatures[0])
