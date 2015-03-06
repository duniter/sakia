'''
Created on 24 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint
from ucoinpy.api import bma

from .node import Node

import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Network(QObject):
    '''
    classdocs
    '''
    nodes_changed = pyqtSignal()

    def __init__(self, currency, nodes):
        '''
        Constructor
        '''
        super().__init__()
        self.currency = currency
        self._nodes = nodes
        for n in self._nodes:
            n.changed.connect(self.nodes_changed)
        self.must_crawl = False

    @classmethod
    def from_json(cls, currency, json_data):
        '''
        We load the nodes which we know for sure since we
        used them at the community creation
        '''
        nodes = []
        for data in json_data:
            node = Node.from_json(currency, data)
            nodes.append(node)
            logging.debug("Loading : {:}".format(data['pubkey']))
        block_max = max([n.block for n in nodes])
        for node in nodes:
            node.check_sync(block_max)
        return cls(currency, nodes)

    def merge_with_json(self, json_data):
        '''
        We merge with dynamic nodes detected when we
        last stopped cutecoin
        '''
        for data in json_data:
            node = Node.from_json(self.currency, data)
            self._nodes.append(node)
            logging.debug("Loading : {:}".format(data['pubkey']))
        self._nodes = self.crawling()

    @classmethod
    def create(cls, node):
        nodes = [node]
        network = cls(node.currency, nodes)
        nodes = network.crawling()
        block_max = max([n.block for n in nodes])
        for node in nodes:
            node.check_sync(block_max)
        network._nodes = nodes
        return network

    def jsonify(self):
        data = []
        for node in self._nodes:
            data.append(node.jsonify())
        return data

    def __del__(self):
        self.must_crawl = False

    def stop_crawling(self):
        self.must_crawl = False

    @property
    def online_nodes(self):
        return [n for n in self._nodes if n.state == Node.ONLINE]

    @property
    def all_nodes(self):
        return self._nodes.copy()

    def add_nodes(self, node):
        self._nodes.append(node)
        node.changed.connect(self.nodes_changed)

    def start_perpetual_crawling(self):
        self.must_crawl = True
        while self.must_crawl:
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

    def crawling(self, interval=0):
        nodes = []
        traversed_pubkeys = []
        for n in self._nodes.copy():
            logging.debug(traversed_pubkeys)
            logging.debug("Peering : next to read : {0} : {1}".format(n.pubkey,
                          (n.pubkey not in traversed_pubkeys)))
            if n.pubkey not in traversed_pubkeys:
                n.peering_traversal(nodes,
                                    traversed_pubkeys, interval)
                time.sleep(interval)

        block_max = max([n.block for n in nodes])
        for node in [n for n in nodes if n.state == Node.ONLINE]:
            node.check_sync(block_max)

        #TODO: Offline nodes for too long have to be removed
        #TODO: Corrupted nodes should maybe be removed faster ?

        logging.debug("Nodes found : {0}".format(nodes))
        return nodes
