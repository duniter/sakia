'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
import re


class Node(object):

    '''
    A ucoin node using BMA protocol
    '''

    def __init__(self, server, port):
        '''
        Constructor
        '''
        self.server = server
        self.port = port

    @classmethod
    def create(cls, server, port):
        return cls(server, port)

    @classmethod
    def load(cls, json_data):
        server = json_data['server']
        port = json_data['port']
        return cls(server, port)

    def __eq__(self, other):
        pubkey = bma.network.Peering(server=self.server,
                                     port=self.port).get()['puubkey']
        other_pubkey = bma.network.Peering(server=other.server,
                                           port=other.port).get()['pubkey']
        return (pubkey == other_pubkey)

    def get_text(self):
        return self.server + ":" + str(self.port)

    def peering(self):
        request = bma.network.Peering(self.connection_handler())
        return request.get()

    def peers(self):
        request = bma.network.peering.Peers(self.connection_handler())
        return request.get()

    def connection_handler(self):
        if self.server is not None:
            return bma.ConnectionHandler(self.server, self.port)
        else:
            return bma.ConnectionHandler(self.ipv4, self.port)

    def jsonify(self):
        return {'server': self.server,
                'port': self.port}
