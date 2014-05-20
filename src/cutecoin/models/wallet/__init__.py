'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import logging
import gnupg
import json
from cutecoin.models.coin import Coin
from cutecoin.models.node import Node
from cutecoin.models.transaction import Transaction
from cutecoin.tools.exceptions import CommunityNotFoundError


class Wallet(object):

    '''
    A wallet is list of coins.
    It's only used to sort coins.
    '''

    def __init__(self, fingerprint, coins, currency, nodes, name):
        '''
        Constructor
        '''
        self.coins = coins
        self.fingerprint = fingerprint
        self.currency = currency
        self.name = name
        self.nodes = nodes

    @classmethod
    def create(cls, fingerprint, currency, node, name):
        node.trust = True
        node.hoster = True
        return cls(fingerprint, [], currency, [node], name)

    @classmethod
    def load(cls, json_data):
        coins = []
        for coinData in json_data['coins']:
            coins.append(Coin.from_id(coinData['coin']))
        fingerprint = json_data['fingerprint']
        name = json_data['name']
        currency = json_data['currency']
        return cls(fingerprint, coins, currency, name)

    def __eq__(self, other):
        return (self.community == other.community)

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    def transactions_received(self):
        received = []
        transactions_data = self.request(
            ucoin.hdc.transactions.Recipient(self.fingerprint))
        for trx_data in transactions_data:
            received.append(
                Transaction.create(
                    trx_data['value']['transaction']['sender'],
                    trx_data['value']['transaction']['number'],
                    self))
        return received

    def transactions_sent(self):
        sent = []
        transactions_data = self.request(
            ucoin.hdc.transactions.sender.Last(
                self.fingerprint, 20))
        for trx_data in transactions_data:
            # Small bug in ucoinpy library
            if not isinstance(trx_data, str):
                sent.append(
                    Transaction.create(
                        trx_data['value']['transaction']['sender'],
                        trx_data['value']['transaction']['number'],
                        self))
        return sent

    def pull_wht(self):
        try:
            wht = self.request(ucoin.network.Wallet(self.fingerprint()))
            return wht['entries']
        except ValueError:
            return None

    def push_wht(self, community):
        hosters_fg = []
        trusts_fg = []
        for trust in self.trusts():
            peering = trust.peering()
            logging.debug(peering)
            trusts_fg.append(peering['fingerprint'])
        for hoster in self.hosters():
            logging.debug(peering)
            peering = hoster.peering()
            hosters_fg.append(peering['fingerprint'])
        entry = {
            'version': '1',
            'currency': self.currency,
            'issuer': self.fingerprint(),
            'requiredTrusts': self.required_trusts,
            'hosters': hosters_fg,
            'trusts': trusts_fg
        }
        logging.debug(entry)
        json_entry = json.JSONEncoder(indent=2).encode(entry)
        gpg = gnupg.GPG()
        signature = gpg.sign(json_entry, keyid=self.keyid, clearsign=True)

        dataPost = {
            'entry': entry,
            'signature': str(signature)
        }

        self.post(ucoin.network.Wallet(
                pgp_fingerprint=self.fingerprint()),
            dataPost)

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
                    found = self._search_node_by_fingerprint(
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

    def trusts(self):
        return [node for node in self.nodes if node.trust]

    def hosters(self):
        return [node for node in self.nodes if node.hoster]

    def get_text(self):
        return self.name + " : " + \
            str(self.value()) + " " + self.currency

    def jsonify_coins_list(self):
        data = []
        for coin in self.coins:
            data.append({'coin': coin.get_id()})
        return data

    def jsonify(self):
        #TODO: Jsonify nodes
        return {'coins': self.jsonify_coins_list(),
                'fingerprint': self.fingerprint,
                'name': self.name,
                'currency': self.currency}
