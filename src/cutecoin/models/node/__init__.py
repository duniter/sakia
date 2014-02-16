'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Node(object):
    '''
    A ucoin node
    '''
    def __init__(self, server, port):
        '''
        Constructor
        '''
        self.server = server
        self.port = port

    def __eq__(self, other):
        return ( self.server == other.server and self.port == other.port )

    def getText(self):
        return self.server + ":" + str(self.port)


class MainNode(Node):
    '''
    MainNode is a node the community is reading to get informations.
    The account sends data one of the community main nodes.
    '''
    def downstreamPeers(self):
        ucoin.settings['server'] = self.server
        ucoin.settings['port'] = self.port

        peers = []
        for peer in ucoin.ucg.peering.peers.DownStream().get()['peers']:
            node = Node(peer['ipv4'], peer['port'])
            peers.append(node)
        return peers

    def use(self, request):
        request.server = self.server
        request.port = self.port
        return request

    def jsonify(self):
        return {'server' : self.server,
                'port' : self.port}

