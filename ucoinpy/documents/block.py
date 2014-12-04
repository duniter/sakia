'''
Created on 2 déc. 2014

@author: inso
'''

from .. import PROTOCOL_VERSION
from . import Document


class Block(Document):
    '''
Version: VERSION
Type: Block
Currency: CURRENCY
Nonce: NONCE
Number: BLOCK_NUMBER
PoWMin: NUMBER_OF_ZEROS
Time: GENERATED_ON
MedianTime: MEDIAN_DATE
UniversalDividend: DIVIDEND_AMOUNT
Issuer: ISSUER_KEY
PreviousHash: PREVIOUS_HASH
PreviousIssuer: PREVIOUS_ISSUER_KEY
Parameters: PARAMETERS
MembersCount: WOT_MEM_COUNT
Identities:
PUBLIC_KEY:SIGNATURE:TIMESTAMP:USER_ID
...
Joiners:
PUBLIC_KEY:SIGNATURE:NUMBER:HASH:TIMESTAMP:USER_ID
...
Actives:
PUBLIC_KEY:SIGNATURE:NUMBER:HASH:TIMESTAMP:USER_ID
...
Leavers:
PUBLIC_KEY:SIGNATURE:NUMBER:HASH:TIMESTAMP:USER_ID
...
Excluded:
PUBLIC_KEY
...
Certifications:
PUBKEY_FROM:PUBKEY_TO:BLOCK_NUMBER:SIGNATURE
...
Transactions:
COMPACT_TRANSACTION
...
BOTTOM_SIGNATURE
    '''

    def __init__(self, currency, noonce, number, powmin, time,
                 mediantime, ud, issuer, prev_hash, prev_issuer,
                 parameters, members_count, identities, joiners,
                 actives, leavers, excluded, certifications,
                 transactions):
        '''
        Constructor
        '''
        self.currency = currency
        self.noonce = noonce
        self.number = number
        self.powmin = powmin
        self.time = time
        self.mediantime = mediantime
        self.ud = ud
        self.issuer = issuer
        self.prev_hash = prev_hash
        self.prev_issuer = prev_issuer
        self.parameters = parameters
        self.members_count = members_count
        self.identities = identities
        self.joiners = joiners
        self.actives = actives
        self.leavers = leavers
        self.excluded = excluded
        self.certifications = certifications
        self.transactions = transactions

    def content(self):
        doc = """
Version: {0}
Type: Block
Currency: {1}
Nonce: {2}
Number: {3}
PoWMin: {4}
Time: {5}
MedianTime: {6}
UniversalDividend: {7}
Issuer: {8}
PreviousHash: {9}
PreviousIssuer: {10}
Parameters: {11}
MembersCount: {12}
Identities:""".format(PROTOCOL_VERSION,
                      self.currency,
                      self.noonce,
                      self.number,
                      self.powmin,
                      self.time,
                      self.mediantime,
                      self.ud,
                      self.issuer,
                      self.prev_hash,
                      self.prev_issuer,
                      self.parameters,
                      self.members_count)

        for identity in self.identities:
            doc += "{0}\n".format(identity.inline())

        doc += "Joiners:\n"
        for joiner in self.joiners:
            doc += "{0}\n".format(joiner.inline())

        doc += "Actives:\n"
        for active in self.actives:
            doc += "{0}\n".format(active.inline())

        doc += "Leavers:\n"
        for leaver in self.leavers:
            doc += "{0]\n".format(leaver.inline())

        doc += "Excluded:\n"
        for exclude in self.exclude:
            doc += "{0}\n".format(exclude.inline())

        doc += "Certifications:\n"
        for cert in self.certifications:
            doc += "{0}\n".format(cert.inline())

        doc += "Transactions:\n"
        for transaction in self.transactions:
            doc += "{0}\n".format(transaction.inline())
