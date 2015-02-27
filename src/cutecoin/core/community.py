'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.documents.block import Block
from ..tools.exceptions import NoPeerAvailable
from .net.node import Node
from .net.network import Network
import logging
import inspect
import hashlib
import re
from requests.exceptions import RequestException


class Cache():
    def __init__(self, community):
        self.latest_block = 0
        self.community = community
        self.data = {}

    def load_from_json(self, data):
        self.data = {}
        for entry in data['cache']:
            key = entry['key']
            cache_key = (key[0], key[1], key[2], key[3], key[4])
            self.data[cache_key] = entry['value']

        self.latest_block = data['latest_block']

    def jsonify(self):
        saved_requests = [hash(bma.blockchain.Block)]
        data = {k: self.data[k] for k in self.data.keys()
                   if k[0] in saved_requests}
        entries = []
        for d in data:
            entries.append({'key': d,
                            'value': data[d]})
        return {'latest_block': self.latest_block,
                'cache': entries}

    def refresh(self):
        self.latest_block = self.community.current_blockid()['number']
        saved_requests = [hash(bma.blockchain.Block)]
        self.data = {k: self.data[k] for k in self.data.keys()
                   if k[0] in saved_requests}

    def request(self, request, req_args={}, get_args={}):
        cache_key = (hash(request),
                     hash(tuple(frozenset(sorted(req_args.keys())))),
                     hash(tuple(frozenset(sorted(req_args.items())))),
                     hash(tuple(frozenset(sorted(get_args.keys())))),
                     hash(tuple(frozenset(sorted(get_args.items())))))

        if cache_key not in self.data.keys():
            result = self.community.request(request, req_args, get_args,
                                         cached=False)

            # Do not cache block 0
            if self.latest_block == 0:
                return result
            else:
                self.data[cache_key] = result
            return self.data[cache_key]
        else:
            return self.data[cache_key]


class Community(object):
    '''
    classdocs
    '''

    def __init__(self, currency, network):
        '''
        A community is a group of nodes using the same currency.
        '''
        self.currency = currency
        self._network = network
        self._cache = Cache(self)

        self._cache.refresh()

    @classmethod
    def create(cls, currency, peer):
        community = cls(currency, [peer])
        logging.debug("Creating community")
        return community

    @classmethod
    def load(cls, json_data):
        currency = json_data['currency']

        network = Network.from_json(currency, json_data['peers'])

        community = cls(currency, network)
        return community

    def load_cache(self, json_data):
        self._cache.load_from_json(json_data)

    def jsonify_cache(self):
        return self._cache.jsonify()

    def name(self):
        return self.currency

    def __eq__(self, other):
        return (other.currency == self.currency)

    @property
    def short_currency(self):
        words = re.split('[_\W]+', self.currency)
        shortened = ""
        if len(words) > 1:
            shortened = ''.join([w[0] for w in words])
        else:
            vowels = ('a', 'e', 'i', 'o', 'u', 'y')
            shortened = self.currency
            shortened = ''.join([c for c in shortened if c not in vowels])
        return shortened.upper()

    @property
    def currency_symbol(self):
        letter = self.currency[0]
        u = ord('\u24B6') + ord(letter) - ord('A')
        return chr(u)

    @property
    def dividend(self):
        block = self.get_ud_block()
        if block:
            return block['dividend']
        else:
            return 1

    def get_ud_block(self, x=0):
        blocks = self.request(bma.blockchain.UD)['result']['blocks']
        if len(blocks) > 0:
            block_number = blocks[len(blocks)-(1+x)]
            block = self.request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block
        else:
            return False

    @property
    def monetary_mass(self):
        try:
            block = self.request(bma.blockchain.Current)
            return block['monetaryMass']
        except ValueError as e:
            if '404' in e:
                return 0

    @property
    def nb_members(self):
        try:
            block = self.request(bma.blockchain.Current)
            return block['membersCount']
        except ValueError as e:
            if '404' in e:
                return 0

    @property
    def nodes(self):
        return self._network.all_nodes

    def add_peer(self, peer):
        self._network.add_node(Node.from_peer(peer))

    def get_block(self, number=None):
        if number is None:
            data = self.request(bma.blockchain.Current)
        else:
            data = self.request(bma.blockchain.Block,
                                req_args={'number': number})

        return Block.from_signed_raw("{0}{1}\n".format(data['raw'],
                                                       data['signature']))

    def current_blockid(self):
        try:
            block = self.request(bma.blockchain.Current, cached=False)
            signed_raw = "{0}{1}\n".format(block['raw'], block['signature'])
            block_hash = hashlib.sha1(signed_raw.encode("ascii")).hexdigest().upper()
            block_number = block['number']
        except ValueError as e:
            if '404' in str(e):
                block_number = 0
                block_hash = "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
            else:
                raise
        return {'number': block_number, 'hash': block_hash}

    def members_pubkeys(self):
        '''
        Listing members pubkeys of a community
        '''
        memberships = self.request(bma.wot.Members)
        return [m['pubkey'] for m in memberships["results"]]

    def refresh_cache(self):
        self._cache.refresh()

    def request(self, request, req_args={}, get_args={}, cached=True):
        if cached:
            return self._cache.request(request, req_args, get_args)
        else:
            nodes = self._network.online_nodes
            for node in nodes:
                try:
                    req = request(node.endpoint.conn_handler(), **req_args)
                    data = req.get(**get_args)

                    if inspect.isgenerator(data):
                        generated = []
                        for d in data:
                            generated.append(d)
                        return generated
                    else:
                        return data
                except ValueError as e:
                    if '502' in str(e):
                        continue
                    else:
                        raise
                except RequestException:
                    continue

        raise NoPeerAvailable(self.currency, len(nodes))

    def post(self, request, req_args={}, post_args={}):
        nodes = self._network.online_nodes
        for node in nodes:
            req = request(node.endpoint.conn_handler(), **req_args)
            logging.debug("Trying to connect to : " + node.pubkey)
            req = request(node.endpoint.conn_handler(), **req_args)
            try:
                req.post(**post_args)
                return
            except ValueError as e:
                raise
            except RequestException:
                continue
        raise NoPeerAvailable(self.currency, len(nodes))

    def broadcast(self, request, req_args={}, post_args={}):
        tries = 0
        ok = False
        value_error = None
        nodes = self._network.online_nodes
        for node in nodes:
            logging.debug("Trying to connect to : " + node.pubkey)
            req = request(node.endpoint.conn_handler(), **req_args)
            try:
                req.post(**post_args)
                ok = True
            except ValueError as e:
                value_error = e
                continue
            except RequestException:
                tries = tries + 1
                continue

        if not ok:
            raise value_error

        if tries == len(self.peers):
            raise NoPeerAvailable(self.currency, len(nodes))

    def jsonify(self):
        data = {'currency': self.currency,
                'peers': self.network.jsonify()}
        return data

    def get_parameters(self):
        return self.request(bma.blockchain.Parameters)
