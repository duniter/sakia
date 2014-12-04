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

    def __init__(self, currency, status, blockid, sender, recipient):
        '''
        Constructor
        '''
        self.currency = currency
        self.status = status
        self.blockid = blockid
        self.sender = sender
        self.recipient = recipient

    def content(self):
        return '''
Version: {0}
Type: Status
Currency: {1}
Status: {2}
Block: {3}
From: {4}
To: {5}
'''.format(PROTOCOL_VERSION, self.currency, self.status,
           self.blockid, self.sender, self.recipient)
