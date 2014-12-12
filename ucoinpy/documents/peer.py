'''
Created on 2 déc. 2014

@author: inso
'''

import re

from . import Document
from .. import PROTOCOL_VERSION, MANAGED_API


class Peer(Document):
    """
    Version: VERSION
    Type: Peer
    Currency: CURRENCY_NAME
    PublicKey: NODE_PUBLICKEY
    Block: BLOCK
    Endpoints:
    END_POINT_1
    END_POINT_2
    END_POINT_3
    [...]
    """

    def __init__(self, version, currency, pubkey, blockid, endpoints, signature):
        super(version, currency, [signature])
        self.pubkey = pubkey
        self.blockid = blockid
        self.endpoints = endpoints

    @classmethod
    def from_raw(cls, raw):
        #TODO : Parsing
        return cls()

    def raw(self):
        doc = """
Version: {0}
Type: Peer
Currency: {1}
PublicKey: {2}
Block: {3}
Endpoints:
""".format(self.version, self.currency, self.pubkey, self.blockid)

        for endpoint in self.endpoints:
            doc += "{0}\n".format(endpoint.inline())

        doc += "{0}\n".format(self.signatures[0])
        return doc


class Endpoint():
    """
    Describing endpoints
    """

    @staticmethod
    def from_inline(inline):
        for api in MANAGED_API:
            if (inline.startswith(api)):
                if (api == "BASIC_MERKLED_API"):
                    return BMAEndpoint.from_inline(inline)


class BMAEndpoint(Endpoint):
    re_inline = re.compile('^BASIC_MERKLED_API( ([a-z_][a-z0-9-_.]+))?( ([0-9.]+))?( ([0-9a-f:]+))?( ([0-9]+))$')

    @classmethod
    def from_inline(cls, inline):
        m = BMAEndpoint.re_inline.match(inline)
        server = m.group(2)
        ipv4 = m.group(4)
        ipv6 = m.group(6)
        port = int(m.group(8))
        return cls(server, ipv4, ipv6, port)

    def __init__(self, server, ipv4, ipv6, port):
        self.server = server
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.port = port

    def inline(self):
        return "BASIC_MERKLED_API {DNS} {IPv4} {IPv6} {PORT}" \
                    .format(DNS=self.server,
                            IPv4=self.ipv4,
                            IPv6=self.ipv6,
                            PORT=self.port)
