import re
import ucoinpy
from .api.bma import ConnectionHandler

HANDLED_API=["BASIC_MERKLED_API"]

class Endpoint():
    """
    Describing endpoints
    """
    def __init__(self, pyendpoint):
        self.pyendpoint = pyendpoint

    @staticmethod
    def from_inline(inline):
        for api in HANDLED_API:
            if (inline.startswith(api)):
                if (api == "BASIC_MERKLED_API"):
                    return BMAEndpoint.from_inline(inline)
        return UnknownEndpoint.from_inline(inline)

    @property
    def server(self):
        return self.pyendpoint.server

    @property
    def ipv4(self):
        return self.pyendpoint.ipv4

    @property
    def ipv6(self):
        return self.pyendpoint.ipv6

    @property
    def port(self):
        return self.pyendpoint.port


class UnknownEndpoint(Endpoint):

    def __init__(self, pyendpoint):
        super().__init__(pyendpoint)

    @classmethod
    def from_inline(cls, inline):
        endpoint = ucoinpy.documents.peer.UnknownEndpoint.from_inline(inline)
        return cls(endpoint)

    def inline(self):
        self.pyendpoint.inline()


class BMAEndpoint(Endpoint):
    re_inline = re.compile('^BASIC_MERKLED_API(?: ([a-z0-9-_.]*(?:.[a-zA-Z])))?(?: ((?:[0-9.]{1,4}){4}))?(?: ((?:[0-9a-f:]{4,5}){4,8}))?(?: ([0-9]+))$')

    def __init__(self, pyendpoint):
        super().__init__(pyendpoint)

    @classmethod
    def from_inline(cls, inline):
        endpoint = ucoinpy.documents.peer.BMAEndpoint.from_inline(inline)
        return cls(endpoint)

    def inline(self):
        return self.pyendpoint.inline()

    def conn_handler(self, network_manager):
        if self.server:
            return ConnectionHandler(network_manager,
                                     self.pyendpoint.server, self.pyendpoint.port)
        elif self.ipv4:
            return ConnectionHandler(network_manager, self.pyendpoint.ipv4,
                                     self.pyendpoint.port)
        else:
            return ConnectionHandler(network_manager,
                                     self.pyendpoint.ipv6, self.pyendpoint.port)
