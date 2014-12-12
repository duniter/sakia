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

    def __init__(self, version, currency, signatures):
        self.version = version
        self.currency = currency
        self.signatures = signatures
