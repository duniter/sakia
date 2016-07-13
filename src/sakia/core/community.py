"""
Created on 1 févr. 2014

@author: inso
"""

import logging
import re
import math

from PyQt5.QtCore import QObject

from ..tools.exceptions import NoPeerAvailable
from .net.network import Network
from duniterpy.api import bma, errors
from .net.api.bma.access import BmaAccess


class Community(QObject):
    """
    A community is a group of nodes using the same currency.

    .. warning:: The currency name is supposed to be unique in sakia
    but nothing exists in duniter to assert that a currency name is unique.
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
    def load(cls, json_data, file_version):
        """
        Load a community from json

        :param dict json_data: The community as a dict in json format
        :param NormalizedVersion file_version: the file sakia version
        """
        currency = json_data['currency']
        network = Network.from_json(currency, json_data['peers'], file_version)
        bma_access = BmaAccess.create(network)
        community = cls(currency, network, bma_access)
        return community

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

    async def dividend(self, block_number=None):
        """
        Get the last generated community universal dividend before block_number.
        If block_number is None, returns the last block_number.

        :param int block_number: The block at which we get the latest dividend

        :return: The last UD or 1 if no UD was generated.
        """
        block = await self.get_ud_block(block_number=block_number)
        if block:
            return block['dividend'] * math.pow(10, block['unitbase'])
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

    async def get_ud_block(self, x=0, block_number=None):
        """
        Get a block with universal dividend
        If x and block_number are passed to the result,
        it returns the 'x' older block with UD in it BEFORE block_number

        :param int x: Get the 'x' older block with UD in it
        :param int block_number: Get the latest dividend before this block number
        :return: The last block with universal dividend.
        :rtype: dict
        """
        try:
            udblocks = await self.bma_access.future_request(bma.blockchain.UD)
            blocks = udblocks['result']['blocks']
            if block_number:
                blocks = [b for b in blocks if b <= block_number]
            if len(blocks) > 0:
                index = len(blocks) - (1+x)
                if index < 0:
                    index = 0
                block_number = blocks[index]
                block = await self.bma_access.future_request(bma.blockchain.Block,
                                     req_args={'number': block_number})
                return block
            else:
                return None
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
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
        block_number = self.network.current_blockUID.number
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
            block_number = self.network.current_blockUID.number
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['membersCount']
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                return 0
        except NoPeerAvailable as e:
            logging.debug(str(e))
            return 0

    async def time(self, block_number=None):
        """
        Get the blockchain time
        :param block_number: The block number, None if current block
        :return: The community blockchain time
        :rtype: int
        """
        try:
            # Get cached block by block number
            if block_number is None:
                block_number = self.network.current_blockUID.number
            block = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['medianTime']
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                return 0
        except NoPeerAvailable as e:
            logging.debug(str(e))
            return 0

    @property
    def network(self):
        """
        Get the community network instance.

        :return: The community network instance.
        :rtype: sakia.core.net.Network
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

    async def certification_expired(self, cert_time):
        """
        Return True if the certificaton time is too old

        :param int cert_time: the timestamp of the certification
        """
        parameters = await self.parameters()
        blockchain_time = await self.time()
        return blockchain_time - cert_time > parameters['sigValidity']

    async def certification_writable(self, cert_time):
        """
        Return True if the certificaton time is too old

        :param int cert_time: the timestamp of the certification
        """
        parameters = await self.parameters()
        blockchain_time = await self.time()
        return blockchain_time - cert_time < parameters['sigWindow'] * parameters['avgGenTime']

    def add_node(self, node):
        """
        Add a peer to the community.

        :param peer: The new peer as a duniterpy Peer object.
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
            block_number = self.network.current_blockUID.number
            data = await self.bma_access.future_request(bma.blockchain.Block,
                                 req_args={'number': block_number})
        else:
            logging.debug("Requesting block {0}".format(number))
            data = await self.bma_access.future_request(bma.blockchain.Block,
                                req_args={'number': number})
        return data

    async def members_pubkeys(self):
        """
        Listing members pubkeys of a community

        :return: All members pubkeys.
        """
        memberships = await self.bma_access.future_request(bma.wot.Members)
        return [m['pubkey'] for m in memberships["results"]]

    def start_coroutines(self):
        self.network.start_coroutines()

    async def stop_coroutines(self, closing=False):
        await self.network.stop_coroutines(closing)

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
