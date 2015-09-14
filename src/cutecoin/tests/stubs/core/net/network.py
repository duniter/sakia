"""
Created on 24 févr. 2015

@author: inso
"""
import asyncio

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject


class Network(QObject):
    """
    A network is managing nodes polling and crawling of a
    given community.
    """
    nodes_changed = pyqtSignal()
    new_block_mined = pyqtSignal(int)

    def __init__(self, currency, nodes):
        """
        Constructor of a network

        :param str currency: The currency name of the community
        :param list nodes: The root nodes of the network
        """
        super().__init__()
        self.currency = currency

    @classmethod
    def create(cls, node):
        nodes = [node]
        network = cls(node.currency, nodes)
        return network

    def merge_with_json(self, json_data):
        pass

    @classmethod
    def from_json(cls, currency, json_data):
        nodes = []
        network = cls(currency, nodes)
        return network

    def jsonify(self):
        data = []
        return data

    @property
    def quality(self):
        return 0.33

    def stop_coroutines(self):
        pass

    def continue_crawling(self):
        return False

    @property
    def synced_nodes(self):
        return self.nodes

    @property
    def online_nodes(self):
        return self.nodes

    @property
    def nodes(self):
        """
        Get all knew nodes.
        """
        return self._nodes

    @property
    def root_nodes(self):
        return self._root_nodes

    @property
    def latest_block(self):
        return 20000

    def add_node(self, node):
        pass

    def add_root_node(self, node):
        pass

    def remove_root_node(self, index):pass

    def is_root_node(self, node):
        return True

    def root_node_index(self, index):
        return self.nodes[0]

    @asyncio.coroutine
    def discover_network(self):
        pass
