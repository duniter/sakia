'''
Created on 2 déc. 2014

@author: inso
'''
from .. import PROTOCOL_VERSION


class Membership(object):
    '''
    This is a utility class to generate membership documents :
    Version: VERSION
    Type: Membership
    Currency: CURRENCY_NAME
    Issuer: ISSUER
    Block: NUMBER-HASH
    Membership: MEMBERSHIP_TYPE
    UserID: USER_ID
    CertTS: CERTIFICATION_TS
    '''

    def __init__(self, currency, issuer, block_number, block_hash,
                 membership_type, userid, cert_ts):
        '''
        Constructor
        '''
        self.currency = currency
        self.issuer = issuer
        self.block_number = block_number
        self.block_hash = block_hash
        self.membership_type = membership_type
        self.userid = userid
        self.cert_ts = cert_ts

    @classmethod
    def from_inline(cls, inline):
        #TODO: Parsing
        return None

    @classmethod
    def from_raw(cls, raw):
        #TODO : Parsing
        return cls()

    def content(self):
        return """
Version: {0}
Type: Membership
Currency: {1}
Issuer: {2}
Block: {3}-{4}
Membership: {5}
UserID: {6}
CertTS: {7}""".format(PROTOCOL_VERSION,
                      self.currency,
                      self.issuer,
                      self.block_number, self.block_hash,
                      self.membership_type,
                      self.userid,
                      self.cert_ts)

    def inline(self):
        return "{0}:{1}:{2}:{3}".format(self.issuer,
                                        self.sign(),
                                        self.block_number,
                                        self.block_hash,
                                        self.cert_ts)
