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
from cutecoin.models.community.network import CommunityNetwork


class Community(object):

    '''
    classdocs
    '''

    def __init__(self, network):
        '''
        A community is a group of nodes using the same currency.
        They are all using the same amendment and are syncing their datas.
        An account is a member of a community if he is a member of the current amendment.
        '''
        self.network = network
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        self.currency = current_amendment['currency']

    @classmethod
    def create(cls, main_node):
        nodes = []
        nodes.append(main_node)
        return cls(CommunityNetwork(nodes))

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

        community = cls(CommunityNetwork(known_nodes))

        for wallets_data in json_data['wallets']:
            wallet = Wallet.load(wallets_data, community)
            wallet.refreshCoins(account.fingerprint())
            account.wallets.wallets_list.append(wallet)
        return community

    def name(self):
        return self.currency

    def __eq__(self, other):
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        current_amendment_hash = hashlib.sha1(
            current_amendment['raw'].encode('utf-8')).hexdigest().upper()

        other_amendment = other.network.request(ucoin.hdc.amendments.Current())
        other_amendment_hash = hashlib.sha1(
            other_amendment['raw'].encode('utf-8')).hexdigest().upper()

        return (other_amendment_hash == current_amendment_hash)

    def dividend(self):
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        return current_amendment['dividend']

    def coin_minimal_power(self):
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        if 'coinMinimalPower' in current_amendment.keys():
            return current_amendment['coinMinimalPower']
        else:
            return 0

    def amendment_id(self):
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        current_amendment_hash = hashlib.sha1(
            current_amendment['raw'].encode('utf-8')).hexdigest().upper()
        amendment_id = str(
            current_amendment["number"]) + "-" + current_amendment_hash
        logging.debug("Amendment : " + amendment_id)
        return amendment_id

    def amendment_number(self):
        current_amendment = self.network.request(ucoin.hdc.amendments.Current())
        return current_amendment['number']

    def person_quality(self, fingerprint):
        if (fingerprint in self.voters_fingerprints()):
            return "voter"
        elif (fingerprint in self.members_fingerprints()):
            return "member"
        else:
            return "nothing"

    def members_fingerprints(self):
        '''
        Listing members of a community
        '''
        fingerprints = self.network.request(
            ucoin.hdc.amendments.view.Members(
                self.amendment_id()))
        members = []
        for f in fingerprints:
            members.append(f['value'])
        return members

    def voters_fingerprints(self):
        '''
        Listing members of a community
        '''
        fingerprints = self.network.request(
            ucoin.hdc.amendments.view.Voters(
                self.amendment_id()))
        voters = []
        for f in fingerprints:
            voters.append(f['value'])
        return voters

    def jsonify_nodes_list(self):
        data = []
        for node in self.network.nodes:
            data.append(node.jsonify())
        return data

    def jsonify(self, wallets):
        data = {'nodes': self.jsonify_nodes_list(),
                'currency': self.currency,
                'wallets': wallets.jsonify(self)}
        return data
