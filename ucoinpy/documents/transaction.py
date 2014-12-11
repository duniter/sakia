'''
Created on 2 déc. 2014

@author: inso
'''

from . import Document
from .. import PROTOCOL_VERSION


class Transaction(Document):
    '''
Version: VERSION
Type: Transaction
Currency: CURRENCY_NAME
Issuers:
PUBLIC_KEY
...
Inputs:
INDEX:SOURCE:NUMBER:FINGERPRINT:AMOUNT
...
Outputs:
PUBLIC_KEY:AMOUNT
...
Comment: COMMENT
SIGNATURES
...
    '''

    def __init__(self, currency, pubkeys, inputs, outputs, comment=None):
        '''
        Constructor
        '''
        self.currency = currency
        self.pubkeys = pubkeys
        self.inputs = inputs
        self.outputs = outputs
        self.comment = comment

    @classmethod
    def from_raw(cls, raw):
        #TODO : Parsing
        return cls()

    def content(self):
        doc = """
Version: {0}
Type: Transaction
Currency: {1}
Issuers:""".format(PROTOCOL_VERSION,
                   self.currency)

        for p in self.pubkeys:
            doc += "{0}\n".format(p)

        doc += "Inputs:\n"
        for i in self.inputs:
            doc += "{0}\n".format(i.inline())

        doc += "Outputs:\n"
        for o in self.outputs:
            doc += "{0}\n".format(o.inline())

        doc += """
COMMENT:
{0}
""".format(self.comment)

        return doc

    def compact(self):
        '''
        Return a transaction in its compact format.
        '''
        """TX:VERSION:NB_ISSUERS:NB_INPUTS:NB_OUTPUTS:HAS_COMMENT
PUBLIC_KEY:INDEX
...
INDEX:SOURCE:FINGERPRINT:AMOUNT
...
PUBLIC_KEY:AMOUNT
...
COMMENT
"""
        doc = "TX:{0}:{1}:{2}:{3}:{4}".format(PROTOCOL_VERSION,
                                              self.pubkeys.len,
                                              self.inputs.len,
                                              self.outputs.len,
                                              '1' if self.Comment else '0')
        for pubkey in self.pubkeys:
            doc += "{0}\n".format(pubkey)
        for i in self.inputs:
            doc += "{0}\n".format(i.compact())
        for o in self.outputs:
            doc += "{0}\n".format(o.inline())
        if self.comment:
            doc += "{0}\n".format(self.comment)
        return doc

    def sign(self, keys):
        signatures = ""
        for k in keys:
            signatures += "{0}\n".format(super().sign(k))
        return signatures


class SimpleTransaction(Transaction):
    '''
As transaction class, but for only one issuer.
...
    '''
    def __init__(self, currency, pubkey, single_input, outputs, comment):
        '''
        Constructor
        '''
        self.currency = currency
        self.pubkeys = [pubkey]
        self.inputs = [single_input]
        self.outputs = outputs
        self.comment = comment


class InputSource():
    '''
    A Transaction INPUT
    '''
    def __init__(self, index, source, number, fingerprint, amount):
        self.index = index
        self.source = source
        self.number = number
        self.fingerprint = fingerprint
        self.amount = amount

    def inline(self):
        return "{0}:{1}:{2}:{3}:{4}".format(self.index,
                                            self.source,
                                            self.number,
                                            self.fingerprint,
                                            self.amount)

    def compact(self):
        return "{0}:{1}:{2}:{3}".format(self.index,
                                        self.source,
                                        self.fingerprint,
                                        self.amount)


class OutputSource():
    '''
    A Transaction OUTPUT
    '''
    def __init__(self, pubkey, amount):
        self.pubkey = pubkey
        self.amount = amount

    def inline(self):
        return "{0}:{1}".format(self.pubkey, self.amount)
