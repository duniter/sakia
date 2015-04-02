'''
Created on 24 févr. 2015

@author: inso
'''
from .node import Node

import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    '''
    A network is managing nodes polling and crawling of a
    given community.
    '''
    nodes_changed = pyqtSignal()
    stopped_perpetual_crawling = pyqtSignal()

    def __init__(self, currency, nodes):
        '''
        Constructor of a network

        :param str currency: The currency name of the community
        :param list nodes: The nodes of the network
        '''
        super().__init__()
        self.currency = currency
        self._nodes = nodes
        for n in self._nodes:
            n.changed.connect(self.nodes_changed)
        self._must_crawl = False
        self._is_perpetual = False

    @classmethod
    def create(cls, node):
        '''
        Create a new network with one knew node
        Crawls the nodes from the first node to build the
        community network

        :param node: The first knew node of the network
        '''
        nodes = [node]
        network = cls(node.currency, nodes)
        nodes = network.crawling()
        block_max = max([n.block for n in nodes])
        for node in nodes:
            node.check_sync(block_max)
        network._nodes = nodes
        return network

    def merge_with_json(self, json_data):
        '''
        We merge with knew nodes when we
        last stopped cutecoin

        :param dict json_data: Nodes in json format
        '''
        for data in json_data:
            node = Node.from_json(self.currency, data)
            self._nodes.append(node)
            logging.debug("Loading : {:}".format(data['pubkey']))
        for n in self._nodes:
            try:
                n.changed.disconnect()
            except TypeError:
                pass
        self._nodes = self.crawling()
        for n in self._nodes:
            n.changed.connect(self.nodes_changed)

    @classmethod
    def from_json(cls, currency, json_data):
        '''
        Load a network from a configured community

        :param str currency: The currency name of a community
        :param dict json_data: A json_data view of a network
        '''
        nodes = []
        for data in json_data:
            node = Node.from_json(currency, data)
            nodes.append(node)
        block_max = max([n.block for n in nodes])
        for node in nodes:
            node.check_sync(block_max)
        return cls(currency, nodes)

    def jsonify(self):
        '''
        Get the network in json format.

        :return: The network as a dict in json format.
        '''
        data = []
        for node in self._nodes:
            data.append(node.jsonify())
        return data

    def stop_crawling(self):
        '''
        Stop network nodes crawling.
        '''
        self._must_crawl = False

    def continue_crawling(self):
        if self._is_perpetual:
            return self._must_crawl
        else:
            return True

    @property
    def synced_nodes(self):
        '''
        Get nodes which are in the ONLINE state.
        '''
        return [n for n in self._nodes if n.state == Node.ONLINE]

    @property
    def online_nodes(self):
        '''
        Get nodes which are in the ONLINE state.
        '''
        return [n for n in self._nodes if n.state in (Node.ONLINE, Node.DESYNCED)]

    @property
    def all_nodes(self):
        '''
        Get all knew nodes.
        '''
        return self._nodes.copy()

    def add_nodes(self, node):
        '''
        Add a node to the network.
        '''
        self._nodes.append(node)
        node.changed.connect(self.nodes_changed)

    def start_perpetual_crawling(self):
        '''
        Start crawling which never stops.
        To stop this crawling, call "stop_crawling" method.
        '''
        self._must_crawl = True
        while self.continue_crawling():
            nodes = self.crawling(interval=10)

            new_inlines = [n.endpoint.inline() for n in nodes]
            last_inlines = [n.endpoint.inline() for n in self._nodes]

            hash_new_nodes = hash(tuple(frozenset(sorted(new_inlines))))
            hash_last_nodes = hash(tuple(frozenset(sorted(last_inlines))))

            if hash_new_nodes != hash_last_nodes:
                self._nodes = nodes
                self.nodes_changed.emit()
                for n in self._nodes:
                    n.changed.connect(self.nodes_changed)
        self.stopped_perpetual_crawling.emit()

    def crawling(self, interval=0):
        '''
        One network crawling.

        :param int interval: The interval between two nodes request.
        '''
        nodes = []
        traversed_pubkeys = []
        for n in self._nodes.copy():
            logging.debug(traversed_pubkeys)
            logging.debug("Peering : next to read : {0} : {1}".format(n.pubkey,
                          (n.pubkey not in traversed_pubkeys)))
            if n.pubkey not in traversed_pubkeys and self.continue_crawling():
                n.peering_traversal(nodes,
                                    traversed_pubkeys, interval,
                                    self.continue_crawling)
                time.sleep(interval)

        block_max = max([n.block for n in nodes])
        for node in [n for n in nodes if n.state == Node.ONLINE]:
            node.check_sync(block_max)

        for node in nodes:
            if node.last_change + 3600 < time.time() and \
                node.state in (Node.OFFLINE, Node.CORRUPTED):
                try:
                    node.changed.disconnect()
                except TypeError:
                    logging.debug("Error : {0} not connected".format(node.pubkey))
                    pass
                nodes.remove(node)

        for node in nodes:
            logging.debug("Syncing : {0} : last changed {1} : unsynced : {2}".format(node.pubkey[:5],
                                                            node.last_change, time.time() - node.last_change))
        logging.debug("Nodes found : {0}".format(nodes))
        return nodes
