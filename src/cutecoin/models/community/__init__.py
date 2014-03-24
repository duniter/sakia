'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import hashlib
import json
import logging
from cutecoin.models.node import Node
from cutecoin.models.wallet import Wallet


class Community(object):

    '''
    classdocs
    '''

    def __init__(self, nodes):
        '''
        A community is a group of nodes using the same currency.
        They are all using the same amendment and are syncing their datas.
        An account is a member of a community if he is a member of the current amendment.
        '''
        self.nodes = nodes
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        self.currency = current_amendment['currency']

    @classmethod
    def create(cls, main_node):
        nodes = []
        nodes.append(main_node)
        return cls(nodes)

    @classmethod
    def load(cls, json_data, account):
        known_nodes = []
        for node_data in json_data['nodes']:
            known_nodes.append(
                Node(
                    node_data['server'],
                    node_data['port'],
                    node_data['trust'],
                    node_data['hoster']))

        community = cls(known_nodes)

        for wallets_data in json_data['wallets']:
            wallet = Wallet.load(wallets_data, community)
            wallet.refreshCoins(account.key_fingerprint())
            account.wallets.wallets_list.append(wallet)
        return community

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

    def pull_tht(self, fingerprint):
        tht = self.ucoin_request(ucoin.ucg.THT(fingerprint))
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

    def trusts(self):
        return [node for node in self.nodes if node.trust]

    def hosters(self):
        return [node for node in self.nodes if node.trust]

    def members_fingerprints(self):
        '''
        Listing members of a community
        '''
        fingerprints = self.ucoin_request(
            ucoin.hdc.amendments.view.Members(
                self.amendment_id()))
        members = []
        for f in fingerprints:
            members.append(f['value'])
        return members

    def ucoin_request(self, request, get_args={}):
        for node in self.trusts():
            logging.debug("Trying to connect to : " + node.getText())
            request = node.use(request)
            return request.get(**get_args)
        raise RuntimeError("Cannot connect to any node")

    def ucoin_post(self, request, get_args={}):
        for node in self.hosters():
            logging.debug("Trying to connect to : " + node.getText())
            request = node.use(request)
            return request.post(**get_args)
        raise RuntimeError("Cannot connect to any node")

    def amendment_id(self):
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        current_amendment_hash = hashlib.sha1(
            current_amendment['raw'].encode('utf-8')).hexdigest().upper()
        amendment_id = str(
            current_amendment["number"]) + "-" + current_amendment_hash
        logging.debug("Amendment : " + amendment_id)
        return amendment_id

    def __eq__(self, other):
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        current_amendment_hash = hashlib.sha1(
            current_amendment['raw'].encode('utf-8')).hexdigest().upper()

        other_amendment = other.ucoin_request(ucoin.hdc.amendments.Current())
        other_amendment_hash = hashlib.sha1(
            other_amendment['raw'].encode('utf-8')).hexdigest().upper()

        return (other_amendment_hash == current_amendment_hash)

    def name(self):
        return self.currency

    def dividend(self):
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        return current_amendment['dividend']

    def coin_minimal_power(self):
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        if 'coinMinimalPower' in current_amendment.keys():
            return current_amendment['coinMinimalPower']
        else:
            return 0

    def amendment_number(self):
        current_amendment = self.ucoin_request(ucoin.hdc.amendments.Current())
        return current_amendment['number']

    def jsonify_nodes_list(self):
        data = []
        for node in self.nodes:
            data.append(node.jsonify())
        return data

    def jsonify(self, wallets):
        data = {'nodes': self.jsonify_nodeslist(),
                'currency': self.currency,
                'wallets': wallets.jsonify(self)}
        return data
