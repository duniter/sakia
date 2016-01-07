import networkx
import logging
from PyQt5.QtCore import QPoint, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene

from ..edges import ExplorerEdge
from ..nodes import ExplorerNode

from .base_scene import BaseScene


class ExplorerScene(BaseScene):
    def __init__(self, parent=None):
        """
        Create scene of the graph

        :param parent: [Optional, default=None] Parent view
        """
        super().__init__(parent)

        self.lastDragPos = QPoint()
        self.setItemIndexMethod(QGraphicsScene.NoIndex)

        # list of nodes in scene
        self.nodes = dict()
        #  axis of the scene for debug purpose
        # self.addLine(-100, 0, 100, 0)
        # self.addLine(0, -100, 0, 100)
        self.node_hovered.connect(self.display_path_to)

        # list of nodes in scene
        self.nodes = dict()
        self.edges = dict()
        self.nx_graph = None
        self.identity = None
        #  axis of the scene for debug purpose
        # self.addLine(-100, 0, 100, 0)
        # self.addLine(0, -100, 0, 100)

    def update_wot(self, nx_graph, identity, dist_max):
        """
        draw community graph

        :param networkx.Graph nx_graph: graph to draw
        :param sakia.core.registry.Identity identity: the wot of the identity
        :param dist_max: the dist_max to display
        """
        #  clear scene
        self.clear()
        self.nodes.clear()
        self.edges.clear()
        self.identity = identity
        self.nx_graph = nx_graph
        # Programs available : neato, twopi, circo, fdp,
        # Nice programs : twopi
        try:
            graph_pos = networkx.pygraphviz_layout(nx_graph, prog="twopi")
        except OSError:
            logging.debug("Twopi not found, fallback mode...")
            graph_pos = networkx.spring_layout(nx_graph, scale=len(nx_graph.nodes())*12)

        # create networkx graph
        for node in nx_graph.nodes(data=True):
            distance = networkx.shortest_path_length(nx_graph.to_undirected(), identity.pubkey, node[0])
            v = ExplorerNode(node, graph_pos, distance, dist_max)
            self.addItem(v)
            self.nodes[node[0]] = v

        for edge in nx_graph.edges(data=True):
            edge[2]["confirmation_text"] = ""
            distance = max(self.nodes[edge[0]].steps, self.nodes[edge[1]].steps)
            explorer_edge = ExplorerEdge(edge[0], edge[1], edge[2], graph_pos, distance, dist_max)
            self.addItem(explorer_edge)
            self.edges[(edge[0], edge[1])] = explorer_edge

        self.update()

    def display_path_to(self, node_id):
        if node_id != self.identity.pubkey:
            path = networkx.shortest_path(self.nx_graph.to_undirected(), self.identity.pubkey, node_id)
            for edge in self.edges.values():
                edge.neutralize()

            for node in self.nodes.values():
                node.neutralize()

            for node, next_node in zip(path[:-1], path[1:]):
                if (node, next_node) in self.edges:
                    edge = self.edges[(node, next_node)]
                elif (next_node, node) in self.edges:
                    edge = self.edges[(next_node, node)]
                if edge:
                    edge.highlight()
                    self.nodes[node].highlight()
                    self.nodes[next_node].highlight()
                    logging.debug("Update edge between {0} and {1}".format(node, next_node))