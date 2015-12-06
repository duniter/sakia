"""
Created on 1 févr. 2014

@author: inso
"""

import logging
import hashlib
import re
import time
import asyncio
import math

from PyQt5.QtCore import QObject, pyqtSignal

from ..tools.exceptions import NoPeerAvailable
from .net.network import Network
from ucoinpy.api import bma
from ucoinpy.documents import Block, BlockId
from .net.api.bma.access import BmaAccess


class Community(QObject):
    """
    A community is a group of nodes using the same currency.

    .. warning:: The currency name is supposed to be unique in sakia
    but nothing exists in ucoin to assert that a currency name is unique.
    """
    def __init__(self, currency, network, bma_access):
        """
        Initialize community attributes with a currency and a network.

        :param str currency: The currency name of the community.
        :param sakia.core.net.network.Network network: The network of the community
        :param sakia.core.net.api.bma.access.BmaAccess bma_access: The BMA Access object

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
    def load(cls, json_data):
        """
        Load a community from json

        :param dict json_data: The community as a dict in json format
        """
        currency = json_data['currency']
        network = Network.from_json(currency, json_data['peers'])
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

    async def dividend(self):
        """
        Get the last generated community universal dividend.

        :return: The last UD or 1 if no UD was generated.
        """
        block = await self.get_ud_block()
        if block:
            return block['dividend']
        else:
            return 1

    async def computed_dividend(self):
        """
        Get the computed community universal dividend.

        Calculation based on t = last UD block time and on values from the that block :

        UD(computed) = CEIL(MAX(UD(t) ; c * M(t) / N(t)))

        :return: The computed UD or 1 if no UD was generated.
        """
        block = await self.get_ud_block()
        if block:
            parameters = await self.parameters()
            return math.ceil(
                max(
                    (await self.dividend()),
                    float(0) if block['membersCount'] == 0 else
                    parameters['c'] * block['monetaryMass'] / block['membersCount']
                )
            )

        else:
            return 1

    async def get_ud_block(self, x=0):
        """
        Get a block with universal dividend

        :param int x: Get the 'x' older block with UD in it
        :return: The last block with universal dividend.
        """
        try:
            udblocks = await self.bma_access.future_request(bma.blockchain.UD)
            blocks = udblocks['result']['blocks']
            if len(blocks) > 0:
                index = len(blocks)-(1+x)
                if index < 0:
                    index = 0
                block_number = blocks[index]
                block = await self.bma_access.future_request(bma.blockchain.Block,
                                     req_args={'number': block_number})
                return block
            else:
                return None
        except ValueError as e:
            if '404' in e:
                logging.debug(str(e))
                return None
        except NoPeerAvailable as e:
            logging.debug(str(e))
            return None

    async def monetary_mass(self):
        """
        Get the community monetary mass

        :return: The monetary mass value
        """
        # Get cached block by block number
        block_number = self.network.current_blockid.number
        if block_number:
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['monetaryMass']
        else:
            return 0

    async def nb_members(self):
        """
        Get the community members number

        :return: The community members number
        """
        try:
            # Get cached block by block number
            block_number = self.network.current_blockid.number
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['membersCount']
        except ValueError as e:
            if '404' in e:
                return 0
        except NoPeerAvailable as e:
            logging.debug(str(e))
            return 0

    async def time(self):
        """
        Get the blockchain time
        :return: The community blockchain time
        :rtype: int
        """
        try:
            # Get cached block by block number
            block_number = self.network.current_blockid.number
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['medianTime']
        except ValueError as e:
            if '404' in e:
                return 0
        except NoPeerAvailable as e:
            logging.debug(str(e))
            return 0

    @property
    def network(self):
        """
        Get the community network instance.

        :return: The community network instance.
        :rtype: sakia.core.net.network.Network
        """
        return self._network

    @property
    def bma_access(self):
        """
        Get the community bma_access instance

        :return: The community bma_access instace
        :rtype: sakia.core.net.api.bma.access.BmaAccess
        """
        return self._bma_access

    async def parameters(self):
        """
        Return community parameters in bma format
        """
        return await self.bma_access.future_request(bma.blockchain.Parameters)

    async def certification_expired(self, certtime):
        """
        Return True if the certificaton time is too old
        """
        parameters = await self.parameters()
        blockchain_time = await self.time()
        return blockchain_time - certtime > parameters['sigValidity']

    def add_node(self, node):
        """
        Add a peer to the community.

        :param peer: The new peer as a ucoinpy Peer object.
        """
        self._network.add_root_node(node)

    def remove_node(self, index):
        """
        Remove a node from the community.

        :param index: The index of the removed node.
        """
        self._network.remove_root_node(index)

    async def get_block(self, number=None):
        """
        Get a block

        :param int number: The block number. If none, returns current block.
        """
        if number is None:
            block_number = self.network.current_blockid.number
            data = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
        else:
            logging.debug("Requesting block {0}".format(number))
            data = await self.bma_access.future_request(bma.blockchain.Block,
                                req_args={'number': number})
        return data

    async def blockid(self):
        """
        Get the block id.

        :return: The current block ID as [NUMBER-HASH] format.
        """
        try:
            block_number = self.network.current_blockid.number
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            signed_raw = "{0}{1}\n".format(block['raw'], block['signature'])
        except ValueError as e:
            if '404' in str(e):
                return BlockId.empty()

        return Block.from_signed_raw(signed_raw).blockid

    async def members_pubkeys(self):
        """
        Listing members pubkeys of a community

        :return: All members pubkeys.
        """
        memberships = await self.bma_access.future_request(bma.wot.Members)
        return [m['pubkey'] for m in memberships["results"]]

    def start_coroutines(self):
        self.network.start_coroutines()

    def stop_coroutines(self):
        self.network.stop_coroutines()

    def rollback_cache(self):
        self._bma_access.rollback()

    def jsonify(self):
        """
        Jsonify the community datas.

        :return: The community as a dict in json format.
        """

        nodes_data = []
        for node in self._network.root_nodes:
            nodes_data.append(node.jsonify_root_node())

        data = {'currency': self.currency,
                'peers': nodes_data}
        return data
