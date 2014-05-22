'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import logging
import gnupg
import json
import time
import importlib
from cutecoin.models.coin import Coin
from cutecoin.models.coin import algorithms
from cutecoin.models.node import Node
from cutecoin.models.transaction import Transaction
from cutecoin.tools.exceptions import AlgorithmNotImplemented


class Wallet(object):

    '''
    A wallet is list of coins.
    It's only used to sort coins.
    '''

    def __init__(self, keyid, currency,
                 nodes, required_trusts, name):
        '''
        Constructor
        '''
        self.coins = []
        self.keyid = keyid
        self.currency = currency
        self.name = name
        self.nodes = nodes
        self.required_trusts = required_trusts
        self.amendments_cache = {}

    @classmethod
    def create(cls, keyid, currency, node, required_trusts, name):
        node.trust = True
        node.hoster = True
        return cls(keyid, currency, [node], required_trusts, name)

    @classmethod
    def load(cls, json_data):
        nodes = []

        for node_data in json_data['nodes']:
            nodes.append(Node.load(node_data))

        keyid = json_data['keyid']
        name = json_data['name']
        currency = json_data['currency']
        required_trusts = json_data['required_trusts']
        return cls(keyid, currency, nodes, required_trusts, name)

    def __eq__(self, other):
        return (self.community == other.community)

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value(self)
        return value

    #TODO: Enhance this code. Loading the amendment each time we load a coin is bad
    def refresh_coins(self):
        self.coins = []
        coins_list_request = ucoin.hdc.coins.List(self.fingerprint())
        data = self.request(coins_list_request)
        for coin_data in data['coins']:
            coin = Coin.from_id(self, coin_data)
            self.coins.append(coin)

    def transfer_coins(self, recipient, coins, message):
        #TODO: Do my own wrapper
        transfer = ucoin.wrappers.transactions.Transaction(
            self.fingerprint(),
            recipient.fingerprint,
            coins,
            message,
            keyid=self.keyid,
            server=self.trusts()[0].server,
            port=self.trusts()[0].port)

        wht_request = ucoin.network.Wallet(recipient.fingerprint)
        recipient_wht = self.request(wht_request)
        nodes = self.get_nodes_in_peering(recipient_wht['entry']['trusts'])
        nodes += [h for h in self.hosters() if h not in nodes]
        result = self.broadcast(nodes,
                                ucoin.hdc.transactions.Process(), transfer())
        if result:
            return result

    def transactions_received(self):
        received = []
        transactions_data = self.request(
            ucoin.hdc.transactions.Recipient(self.fingerprint()))
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
                self.fingerprint(), 20))
        for trx_data in transactions_data['transactions']:
            # Small bug in ucoinpy library
            if not isinstance(trx_data, str):
                sent.append(
                    Transaction.create(
                        trx_data['sender'],
                        trx_data['number'],
                        self))
        return sent

    def pull_wht(self):
        wht = self.request(ucoin.network.Wallet(self.fingerprint()))
        if wht is None:
            return []
        else:
            return wht['entry']

    def push_wht(self):
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
        wht_message = '''Version: 1
Currency: %s
Key: %s
Date: %s
RequiredTrusts: %d
Hosters:
''' % (self.currency, self.fingerprint(), int(time.time()),
       self.required_trusts)
        for hoster in hosters_fg:
            wht_message += '''%s\n''' % hoster
        wht_message += '''Trusts:\n'''
        for trust in trusts_fg:
            wht_message += '''%s\n''' % trust

        wht_message = wht_message.replace("\n", "\r\n")
        gpg = gnupg.GPG()
        signature = gpg.sign(wht_message, keyid=self.keyid, detach=True)

        data_post = {'entry': wht_message,
                     'signature': str(signature)}
        logging.debug(data_post)

        self.post(ucoin.network.Wallet(), data_post)

    # TODO: Check if its working
    def _search_node_by_fingerprint(self, node_fg, next_node, traversed_nodes=[]):
        next_fg = next_node.peering()['fingerprint']
        print(traversed_nodes)
        if next_fg not in traversed_nodes:
            traversed_nodes.append(next_fg)
            if node_fg == next_fg:
                return next_node
            else:
                for peer in next_node.peers():
                    # Look for next node informations
                    found = self._search_node_by_fingerprint(
                        node_fg,
                        Node.from_endpoints(peer['value']['endpoints']),
                        traversed_nodes)
                    if found is not None:
                        return found
        return None

    def get_nodes_in_peering(self, fingerprints):
        nodes = []
        for node_fg in fingerprints:
            node = self._search_node_by_fingerprint(
                    node_fg,
                    self.trusts()[0],
                    [])
            if node is not None:
                nodes.append(node)
            #TODO: Check that one trust exists
        return nodes

    def request(self, request, get_args={}):
        error = None
        for node in self.trusts():
            logging.debug("Trying to connect to : " + node.get_text())
            node.use(request)
            try:
                data = request.get(**get_args)
                return data
            except ValueError as e:
                error = str(e)
            except:
                continue
        return error

    def post(self, request, get_args={}):
        error = None
        for node in self.hosters():
            logging.debug("Trying to connect to : " + node.get_text())
            node.use(request)
            try:
                data = request.post(**get_args)
            except ValueError as e:
                error = str(e)
            except:
                continue
            return data
        return error

    def broadcast(self, nodes, request, get_args={}):
        error = None
        for node in nodes:
            logging.debug("Trying to connect to : " + node.get_text())
            node.use(request)
            try:
                request.post(**get_args)
            except ValueError as e:
                error = str(e)
            except:
                continue
        return error

    def trusts(self):
        return [node for node in self.nodes if node.trust]

    def hosters(self):
        return [node for node in self.nodes if node.hoster]

    def get_amendment(self, am_number):
        if am_number in self.amendments_cache:
            return self.amendments_cache[am_number]
        else:
            amendment_req = ucoin.hdc.amendments.Promoted(am_number)
            new_am = self.request(amendment_req)
            self.amendments_cache[am_number] = new_am
            return new_am

    def fingerprint(self):
        gpg = gnupg.GPG()
        available_keys = gpg.list_keys()
        logging.debug(self.keyid)
        for k in available_keys:
            logging.debug(k)
            if k['keyid'] == self.keyid:
                return k['fingerprint']
        return ""

    def get_text(self):
        return self.name + " : " + \
            str(self.value()) + " " + self.currency

    def jsonify_coins_list(self):
        data = []
        for coin in self.coins:
            data.append({'coin': coin.get_id()})
        return data

    def jsonify_nodes_list(self):
        data = []
        for node in self.nodes:
            data.append(node.jsonify())
        return data

    def jsonify(self):
        return {'required_trusts': self.required_trusts,
                'keyid': self.keyid,
                'name': self.name,
                'currency': self.currency,
                'nodes': self.jsonify_nodes_list()}
