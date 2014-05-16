'''
Created on 27 mars 2014

@author: inso
'''
from cutecoin.models.node import Node
import ucoin
import logging

class CommunityNetwork(object):
    '''
    classdocs
    '''

    #TODO: Factory to load json
    def __init__(self, nodes):
        '''
        Constructor
        '''
        self.nodes = nodes

    def request(self, request, get_args={}):
        for node in self.trusts():
            logging.debug("Trying to connect to : " + node.get_text())
            node.use(request)
            return request.get(**get_args)
        raise RuntimeError("Cannot connect to any node")

    def post(self, request, get_args={}):
        for node in self.hosters():
            logging.debug("Trying to connect to : " + node.get_text())
            node.use(request)
            return request.post(**get_args)
        raise RuntimeError("Cannot connect to any node")

    # TODO: Check if its working
    def _search_node_by_fingerprint(self, node_fg, next_node, traversed_nodes=[]):
        next_fg = next_node.peering()['fingerprint']
        if next_fg not in traversed_nodes:
            traversed_nodes.append(next_fg)
            if node_fg == next_fg:
                return next_node
            else:
                for peer in next_node.peers():
                    # Look for next node informations
                    found = self._searchTrustAddresses(
                        node_fg, Node(
                            peer['ipv4'], int(
                                peer['port'])), traversed_nodes)
                    if found is not None:
                        return found
        return None

    def get_nodes_in_peering(self, fingerprints):
        nodes = []
        for node_fg in fingerprints:
            nodes.append(
                self._search_node_by_fingerprint(
                    node_fg,
                    self.trusts()[0]))
        return nodes

    def trusts(self):
        return [node for node in self.nodes if node.trust]

    def hosters(self):
        return [node for node in self.nodes if node.hoster]

#TODO: Manager in Wallets
"""
    def pull_tht(self, fingerprint):
        tht = self.network.request(ucoin.ucg.THT(fingerprint))
        nodes = []
        nodes.append(self.trusts()[0])
        # We add trusts to the node list
        for node_fg in tht['trusts']:
            nodes.append(
                self._search_node_by_fingerprint(
                    node_fg,
                    self.trusts()[0]))
        # We look in hosters lists
        for node_fg in tht['hosters']:
            # If the node was already added as a trust
            if node_fg in tht['trusts']:
                found_nodes = [
                    node for node in nodes if node.peering()['fingerprint'] == node_fg]
                if len(found_nodes) == 1:
                    found_nodes[0].hoster = True
                else:
                    # not supposed to happen
                    pass
            # Else we add it
            else:
                nodes.append(
                    self._search_node_by_fingerprint(
                        node_fg,
                        self.trusts()[0]))
"""
