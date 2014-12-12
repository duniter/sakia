'''
Created on 3 déc. 2014

@author: inso
'''
import base58
import re
from ..key import Base58Encoder


class Document:
    RE_VERSION = re.compile("Version: ([0-9]+)\n")

    def __init__(self, version):
        self.version = version
