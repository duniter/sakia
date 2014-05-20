'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import re


class Node(object):

    '''
    A ucoin node using BMA protocol
    '''

    def __init__(self, server, port, trust, hoster):
        '''
        Constructor
        '''
        self.server = server
        self.port = port
        self.trust = trust
        self.hoster = hoster

    @classmethod
    def create(cls, server, port, trust=False, hoster=False):
        return cls(server, port, trust, hoster)

    @classmethod
    def from_endpoints(cls, endpoints):
        #TODO: Manage multiple endpoints
        for endpoint in endpoints:
            bma_endpoints = re.compile('^BASIC_MERKLED_API( ([a-z_][a-z0-9-_.]+))?( ([0-9.]+))?( ([0-9a-f:]+))?( ([0-9]+))$')
            m = bma_endpoints.match(endpoint)
            server = m.group(4)
            port = int(m.group(8))
        return cls(server, port, False, False)

    @classmethod
    def load(cls, json_data):
        server = json_data['server']
        port = json_data['port']
        trust = json_data['trust']
        hoster = json_data['hoster']
        return cls(server, port, trust, hoster)

    def __eq__(self, other):
        return (self.server == other.server and self.port == other.port)

    def get_text(self):
        return self.server + ":" + str(self.port)

    '''
        TrustedNode is a node the community is reading to get informations.
        The account sends data one of the community main nodes.
    '''

    def downstream_peers(self):
        ucoin.settings['server'] = self.server
        ucoin.settings['port'] = self.port

        peers = []
        for peer in ucoin.network.peering.peers.DownStream().get()['peers']:
            node = Node.create(peer['ipv4'], peer['port'])
            peers.append(node)

        return peers

    def peering(self):
        request = ucoin.network.Peering()
        self.use(request)
        return request.get()

    def peers(self):
        request = ucoin.network.peering.Peers()
        self.use(request)
        return request.get()

    def use(self, request):
        request.server = self.server
        request.port = self.port
        return request

    def jsonify(self):
        return {'server': self.server,
                'port': self.port,
                'trust': self.trust,
                'hoster': self.hoster}
