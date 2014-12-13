'''
Created on 2 déc. 2014

@author: inso
'''

import re
from . import Document


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

    re_type = re.compile("Type: (Status)")
    re_status = re.compile("Status: (NEW|NEW_BACK|UP|UP_BACK|DOWN)")
    re_block = re.compile("Block: ([0-9]+-[0-9a-fA-F]{5,40})\n")
    re_from = re.compile("From: ([1-9A-Za-z][^OIl]{42,45})\n")
    re_to = re.compile("To: ([1-9A-Za-z][^OIl]{42,45})\n")

    def __init__(self, version, currency, status, blockid, sender,
                 recipient, signature):
        '''
        Constructor
        '''
        if signature:
            super().__init__(version, currency, [signature])
        else:
            super().__init__(version, currency, [])

        self.status = status
        self.blockid = blockid
        self.sender = sender
        self.recipient = recipient

    @classmethod
    def from_signed_raw(cls, raw):
        lines = raw.splitlines(True)
        n = 0

        version = int(Status.re_version.match(lines[n]).group(1))
        n = n + 1

        Status.re_type.match(lines[n]).group(1)
        n = n + 1

        currency = Status.re_currency.match(lines[n]).group(1)
        n = n + 1

        status = Status.re_status.match(lines[n]).group(1)
        n = n + 1

        blockid = Status.re_block.match(lines[n]).group(1)
        n = n + 1

        sender = Status.re_from.match(lines[n]).group(1)
        n = n + 1

        recipient = Status.re_to.match(lines[n]).group(1)
        n = n + 1

        signature = Status.re_signature.match(lines[n]).group(1)
        n = n + 1

        return cls(version, currency, status, blockid,
                   sender, recipient, signature)

    def raw(self):
        return '''Version: {0}
Type: Status
Currency: {1}
Status: {2}
Block: {3}
From: {4}
To: {5}
'''.format(self.version, self.currency, self.status,
           self.blockid, self.sender, self.recipient)
