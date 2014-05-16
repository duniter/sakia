'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin


class Node(object):

    '''
    A ucoin node using BMA protocol
    '''

    def __init__(self, server, port, trust=False, hoster=False):
        '''
        Constructor
        '''
        self.server = server
        self.port = port
        self.trust = trust
        self.hoster = hoster

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
            node = Node(peer['ipv4'], peer['port'])
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
