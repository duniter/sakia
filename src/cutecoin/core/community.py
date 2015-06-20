'''
Created on 1 févr. 2014

@author: inso
'''

import logging
import hashlib
import re
import time

from PyQt5.QtCore import QObject, pyqtSignal
from requests.exceptions import RequestException

from ucoinpy.documents.block import Block
from ..tools.exceptions import NoPeerAvailable
from .net.network import Network
from .net.api import bma as qtbma
from .net.api.bma.access import BmaAccess


class Community(QObject):
    """
    A community is a group of nodes using the same currency.

    .. warning:: The currency name is supposed to be unique in cutecoin
    but nothing exists in ucoin to assert that a currency name is unique.
    """
    inner_data_changed = pyqtSignal(str)

    def __init__(self, currency, network, bma_access):
        """
        Initialize community attributes with a currency and a network.

        :param str currency: The currency name of the community.
        :param cutecoin.core.net.network.Network network: The network of the community
        :param cutecoin.core.net.api.bma.access.BmaAccess bma_access: The BMA Access object

        .. warning:: The community object should be created using its factory
        class methods.
        """
        super().__init__()
        self.currency = currency
        self._network = network
        self._bma_access = bma_access

    @classmethod
    def create(cls, node):
        """
        Create a community from its first node.

        :param node: The first Node of the community
        """
        network = Network.create(node)
        bma_access = BmaAccess.create(network)
        community = cls(node.currency, network, bma_access)
        logging.debug("Creating community")
        return community

    @classmethod
    def load(cls, network_manager, json_data):
        """
        Load a community from json

        :param dict json_data: The community as a dict in json format
        """
        currency = json_data['currency']
        network = Network.from_json(network_manager, currency, json_data['peers'])
        bma_access = BmaAccess.create(network)
        community = cls(currency, network, bma_access)
        return community

    def load_cache(self, bma_access_cache, network_cache):
        """
        Load the community cache.

        :param dict bma_access_cache: The BmaAccess cache in json
        :param dict network_cache: The network cache in json
        """
        self._bma_access.load_from_json(bma_access_cache)
        self._network.merge_with_json(network_cache)

    @property
    def name(self):
        """
        The community name is its currency name.

        :return: The community name
        """
        return self.currency

    @property
    def short_currency(self):
        """
        Format the currency name to a short one

        :return: The currency name in a shot format.
        """
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
        """
        Format the currency name to a symbol one.

        :return: The currency name as a utf-8 circled symbol.
        """
        letter = self.currency[0]
        u = ord('\u24B6') + ord(letter) - ord('A')
        return chr(u)

    #@property
    def dividend(self):
        """
        Get the last generated community universal dividend.

        :return: The last UD or 1 if no UD was generated.
        """
        block = self.get_ud_block()
        if block:
            return block['dividend']
        else:
            return 1

    def get_ud_block(self, x=0):
        """
        Get a block with universal dividend

        :param int x: Get the 'x' older block with UD in it
        :return: The last block with universal dividend.
        """
        blocks = self.bma_access.get(self, qtbma.blockchain.UD)['result']['blocks']
        if len(blocks) > 0:
            block_number = blocks[len(blocks)-(1+x)]
            block = self.bma_access.get(self, qtbma.blockchain.Block,
                                 req_args={'number': block_number})
            return block
        else:
            return None

    @property
    def monetary_mass(self):
        """
        Get the community monetary mass

        :return: The monetary mass value
        """
        try:
            # Get cached block by block number
            block_number = self.network.latest_block
            block = self.bma_access.get(self, qtbma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['monetaryMass']
        except ValueError as e:
            if '404' in e:
                return 0
        except NoPeerAvailable as e:
            return 0

    @property
    def nb_members(self):
        """
        Get the community members number

        :return: The community members number
        """
        try:
            # Get cached block by block number
            block_number = self.network.latest_block
            block = self.bma_access.get(qtbma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['membersCount']
        except ValueError as e:
            if '404' in e:
                return 0
        except NoPeerAvailable as e:
            return 0

    @property
    def network(self):
        """
        Get the community network instance.

        :return: The community network instance.
        :rtype: cutecoin.core.net.network.Network
        """
        return self._network

    @property
    def bma_access(self):
        """
        Get the community bma_access instance

        :return: The community bma_access instace
        :rtype: cutecoin.core.net.api.bma.access.BmaAccess
        """
        return self._bma_access

    @property
    def parameters(self):
        """
        Return community parameters in bma format
        """
        return self.bma_access.get(self, qtbma.blockchain.Parameters)

    def certification_expired(self, certtime):
        '''
        Return True if the certificaton time is too old
        '''
        return time.time() - certtime > self.parameters['sigValidity']

    def add_node(self, node):
        '''
        Add a peer to the community.

        :param peer: The new peer as a ucoinpy Peer object.
        '''
        self._network.add_root_node(node)

    def remove_node(self, index):
        '''
        Remove a node from the community.

        :param index: The index of the removed node.
        '''
        self._network.remove_root_node(index)

    def get_block(self, number=None):
        '''
        Get a block

        :param int number: The block number. If none, returns current block.
        '''
        if number is None:
            data = self.bma_access.get(self, qtbma.blockchain.Current)
        else:
            logging.debug("Requesting block {0}".format(number))
            data = self.bma_access.get(self, qtbma.blockchain.Block,
                                req_args={'number': number})
        return data

    def current_blockid(self):
        '''
        Get the current block id.

        :return: The current block ID as [NUMBER-HASH] format.
        '''
        try:
            block = self.bma_access.get(self, qtbma.blockchain.Current, cached=False)
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
        memberships = self.bma_access.get(self, qtbma.wot.Members)
        return [m['pubkey'] for m in memberships["results"]]

    def refresh_cache(self):
        '''
        Start the refresh processing of the cache
        '''
        self._cache.refresh()

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

        if tries == len(nodes):
            raise NoPeerAvailable(self.currency, len(nodes))

    def jsonify(self):
        '''
        Jsonify the community datas.

        :return: The community as a dict in json format.
        '''

        nodes_data = []
        for node in self._network.root_nodes:
            nodes_data.append(node.jsonify_root_node())

        data = {'currency': self.currency,
                'peers': nodes_data}
        return data
