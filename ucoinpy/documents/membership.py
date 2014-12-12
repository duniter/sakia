'''
Created on 2 déc. 2014

@author: inso
'''
from .. import PROTOCOL_VERSION
from . import Document

import re


class Membership(Document):
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

    # PUBLIC_KEY:SIGNATURE:NUMBER:HASH:TIMESTAMP:USER_ID
    re_inline = re.compile("([1-9A-Za-z][^OIl]{43,45}):([A-Za-z0-9+/]+):\
    ([0-9]+):([0-9a-fA-F]{5,40}):([0-9]+):([^\n]+)\n")

    def __init__(self, version, currency, issuer, block_number, block_hash,
                 membership_type, userid, cert_ts, sign):
        '''
        Constructor
        '''
        super(version)
        self.currency = currency
        self.issuer = issuer
        self.block_number = block_number
        self.block_hash = block_hash
        self.membership_type = membership_type
        self.userid = userid
        self.cert_ts = cert_ts
        self.sign = sign

    @classmethod
    def from_inline(cls, version, currency, type, inline):
        data = Membership.re_inline.match(inline)
        issuer = data.group(1)
        sign = data.group(2)
        block_number = data.group(3)
        block_hash = data.group(4)
        cert_ts = data.group(5)
        userid = data.group(6)
        return cls(version, currency, issuer, block_number,
                   block_hash, type, userid, cert_ts, sign)

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
                                        self.sign,
                                        self.block_number,
                                        self.block_hash,
                                        self.cert_ts)
