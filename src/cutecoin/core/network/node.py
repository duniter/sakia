'''
Created on 21 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint
from ucoinpy.api import bma
from ...core.person import Person
from ...tools.exceptions import PersonNotFoundError


class Node(object):
    '''
    classdocs
    '''

    def __init__(self, endpoint, pubkey, block):
        '''
        Constructor
        '''
        self._endpoint = endpoint
        self._pubkey = pubkey
        self._block = block

    @classmethod
    def from_peer(cls, peer):
        e = next((e for e in peer.endpoints if type(e) is BMAEndpoint))
        informations = bma.network.Peering(e.conn_handler()).get()
        try:
            block = bma.blockchain.Current(e.conn_handler()).get()
            block_number = block["number"]
        except ValueError as e:
            if '404' in e:
                block_number = 0
        node_pubkey = informations["pubkey"]

        return cls(e, node_pubkey, block_number)

    @property
    def pubkey(self):
        return self._pubkey

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def block(self):
        return self._block
