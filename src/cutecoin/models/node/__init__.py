'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Node(object):
    '''
    classdocs
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

    def downstreamPeers(self):
        ucoin.settings['server'] = self.server
        ucoin.settings['port'] = self.port

        peers = []
        for peer in ucoin.ucg.peering.peers.DownStream().get()['peers']:
            node = Node(peer['ipv4'], peer['port'])
            peers.append(node)
        return peers

    #TODO: Jsonify this model
    def saveJson(self):
        pass

