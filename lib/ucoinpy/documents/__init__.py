'''
Created on 3 déc. 2014

@author: inso
'''
import base58
import base64
import re
import logging
from ..key import Base58Encoder

class Document:
    re_version = re.compile("Version: ([0-9]+)\n")
    re_currency = re.compile("Currency: ([^\n]+)\n")
    re_signature = re.compile("([A-Za-z0-9+/]+(?:=|==)?)\n")

    def __init__(self, version, currency, signatures):
        self.version = version
        self.currency = currency
        if signatures:
            self.signatures = [s for s in signatures if s is not None]
        else:
            self.signatures = []

    def sign(self, keys):
        '''
        Sign the current document.
        Warning : current signatures will be replaced with the new ones.
        '''
        self.signatures = []
        for key in keys:
            signing = base64.b64encode(key.signature(bytes(self.raw(), 'ascii')))
            logging.debug("Signature : \n{0}".format(signing.decode("ascii")))
            self.signatures.append(signing.decode("ascii"))

    def signed_raw(self):
        '''
        If keys are None, returns the raw + current signatures
        If keys are present, returns the raw signed by these keys
        '''
        raw = self.raw()
        signed = "\n".join(self.signatures)
        signed_raw = raw + signed + "\n"
        return signed_raw
