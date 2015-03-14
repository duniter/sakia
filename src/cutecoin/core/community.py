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
    _saved_requests = [str(bma.blockchain.Block)]

    def __init__(self, community):
        '''
        Init an empty cache
        '''
        self.latest_block = 0
        self.community = community
        self.data = {}

    def load_from_json(self, data):
        '''
        Put data in the cache from json datas.

        :param dict data: The cache in json format
        '''
        self.data = {}
        for entry in data['cache']:
            key = entry['key']
            cache_key = (key[0], key[1], key[2], key[3], key[4])
            self.data[cache_key] = entry['value']

        self.latest_block = data['latest_block']

    def jsonify(self):
        '''
        Get the cache in json format

        :return: The cache as a dict in json format
        '''
        data = {k: self.data[k] for k in self.data.keys()
                   if k[0] in Cache._saved_requests}
        entries = []
        for d in data:
            entries.append({'key': d,
                            'value': data[d]})
        return {'latest_block': self.latest_block,
                'cache': entries}

    def refresh(self):
        '''
        Refreshing the cache just clears every last requests which
        cannot be saved because they can change from one block to another.
        '''
        self.latest_block = self.community.current_blockid()['number']
        self.data = {k: self.data[k] for k in self.data.keys()
                   if k[0] in Cache._saved_requests}

    def request(self, request, req_args={}, get_args={}):
        '''
        Send a cached request to a community.
        If the request was already sent in current block, return last value get.

        :param request: The request bma class
        :param req_args: The arguments passed to the request constructor
        :param get_args: The arguments passed to the requests __get__ method
        '''
        cache_key = (str(request),
                     str(tuple(frozenset(sorted(req_args.keys())))),
                     str(tuple(frozenset(sorted(req_args.items())))),
                     str(tuple(frozenset(sorted(get_args.keys())))),
                     str(tuple(frozenset(sorted(get_args.items())))))

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
    A community is a group of nodes using the same currency.

    .. warning:: The currency name is supposed to be unique in cutecoin
    but nothing exists in ucoin to assert that a currency name is unique.
    '''

    def __init__(self, currency, network):
        '''
        Initialize community attributes with a currency and a network.

        :param str currency: The currency name of the community.
        :param network: The network of the community

        .. warning:: The community object should be created using its factory
        class methods.
        '''
        self.currency = currency
        self._network = network
        self._cache = Cache(self)

        self._cache.refresh()

    @classmethod
    def create(cls, node):
        '''
        Create a community from its first node.

        :param node: The first Node of the community
        '''
        network = Network.create(node)
        community = cls(node.currency, network)
        logging.debug("Creating community")
        return community

    @classmethod
    def load(cls, json_data):
        '''
        Load a community from json

        :param dict json_data: The community as a dict in json format
        '''
        currency = json_data['currency']
        network = Network.from_json(currency, json_data['peers'])
        community = cls(currency, network)
        return community

    def load_merge_network(self, json_data):
        '''
        Load the last state of the network.
        This network is merged with the network currently
        known network.

        :param dict json_data:
        '''
        self._network.merge_with_json(json_data)

    def load_cache(self, json_data):
        '''
        Load the community cache.

        :param dict json_data: The community as a dict in json format.
        '''
        self._cache.load_from_json(json_data)

    def jsonify_cache(self):
        '''
        Get the cache jsonified.

        :return: The cache as a dict in json format.
        '''
        return self._cache.jsonify()

    def jsonify_network(self):
        '''
        Get the network jsonified.
        '''
        return self._network.jsonify()

    @property
    def name(self):
        '''
        The community name is its currency name.

        :return: The community name
        '''
        return self.currency

    def __eq__(self, other):
        '''
        :return: True if this community has the same currency name as the other one.
        '''
        return (other.currency == self.currency)

    @property
    def short_currency(self):
        '''
        Format the currency name to a short one

        :return: The currency name in a shot format.
        '''
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
        '''
        Format the currency name to a symbol one.

        :return: The currency name as a utf-8 circled symbol.
        '''
        letter = self.currency[0]
        u = ord('\u24B6') + ord(letter) - ord('A')
        return chr(u)

    @property
    def dividend(self):
        '''
        Get the last generated community universal dividend.

        :return: The last UD or 1 if no UD was generated.
        '''
        block = self.get_ud_block()
        if block:
            return block['dividend']
        else:
            return 1

    def get_ud_block(self, x=0):
        '''
        Get a block with universal dividend

        :param int x: Get the 'x' older block with UD in it
        :return: The last block with universal dividend.
        '''
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
        '''
        Get the community monetary mass

        :return: The monetary mass value
        '''
        try:
            block = self.request(bma.blockchain.Current)
            return block['monetaryMass']
        except ValueError as e:
            if '404' in e:
                return 0

    @property
    def nb_members(self):
        '''
        Get the community members number

        :return: The community members number
        '''
        try:
            block = self.request(bma.blockchain.Current)
            return block['membersCount']
        except ValueError as e:
            if '404' in e:
                return 0

    @property
    def nodes(self):
        '''
        Get the known community nodes

        :return: All community known nodes
        '''
        return self._network.all_nodes

    @property
    def network(self):
        '''
        Get the community network instance.

        :return: The community network instance.
        '''
        return self._network

    @property
    def parameters(self):
        '''

        '''
        return self.request(bma.blockchain.Parameters)

    @property
    def add_peer(self, peer):
        '''
        Add a peer to the community.

        :param peer: The new peer as a ucoinpy Peer object.
        '''
        self._network.add_node(Node.from_peer(peer))

    def get_block(self, number=None):
        '''
        Get a block

        :param int number: The block number. If none, returns current block.
        '''
        if number is None:
            data = self.request(bma.blockchain.Current)
        else:
            data = self.request(bma.blockchain.Block,
                                req_args={'number': number})

        return Block.from_signed_raw("{0}{1}\n".format(data['raw'],
                                                       data['signature']))

    def current_blockid(self):
        '''
        Get the current block id.

        :return: The current block ID as [NUMBER-HASH] format.
        '''
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

        :return: All members pubkeys.
        '''
        memberships = self.request(bma.wot.Members)
        return [m['pubkey'] for m in memberships["results"]]

    def refresh_cache(self):
        '''
        Start the refresh processing of the cache
        '''
        self._cache.refresh()

    def request(self, request, req_args={}, get_args={}, cached=True):
        '''
        Start a request to the community.

        :param request: A ucoinpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param get_args: Arguments to pass to the request __get__ method
        :return: The returned data
        '''
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
        '''
        Post data to a community.
        Only sends the data to one node.

        :param request: A ucoinpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param post_args: Arguments to pass to the request __post__ method
        :return: The returned data
        '''
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
        '''
        Broadcast data to a community.
        Sends the data to all knew nodes.

        :param request: A ucoinpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param post_args: Arguments to pass to the request __post__ method
        :return: The returned data

        .. note:: If one node accept the requests (returns 200),
        the broadcast is considered accepted by the network.
        '''
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

        if tries == len(self.nodes):
            raise NoPeerAvailable(self.currency, len(nodes))

    def jsonify(self):
        '''
        Jsonify the community datas.

        :return: The community as a dict in json format.
        '''
        data = {'currency': self.currency,
                'peers': self._network.jsonify()}
        return data