'''
Created on 3 déc. 2014

@author: inso
'''
import base58
import re
from ..key import Base58Encoder

class Document:
    re_version = re.compile("Version: ([0-9]+)\n")
    re_currency = re.compile("Currency: ([^\n]+)\n")
    re_signature = re.compile("([A-Za-z0-9+/]+(?:=|==)?)\n")

    def __init__(self, version, currency, signatures):
        self.version = version
        self.currency = currency
        self.signatures = signatures

    def sign(self, keys):
        '''
        Sign the current document.
        Warning : current signatures will be replaced with the new ones.
        '''
        self.signatures = []
        for k in keys:
            self.signatures.append(k.signature(self.raw()))

    def signed_raw(self):
        '''
        If keys are None, returns the raw + current signatures
        If keys are present, returns the raw signed by these keys
        '''
        raw = self.raw()
        signed_raw = raw
        for s in self.signatures:
            if s is not None:
                signed_raw += s + "\n"
        return signed_raw
