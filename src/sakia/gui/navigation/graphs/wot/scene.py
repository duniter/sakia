import networkx
from PyQt5.QtCore import QPoint, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene

from .edge import WotEdge
from .node import WotNode
from sakia.helpers import dpi_ratio

from ..base.scene import BaseScene


class WotScene(BaseScene):
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

    @staticmethod
    def certified_partial_layout(nx_graph, center, scale=1):
        """
        Method to generate a partial wot with certifiers layout
        :param networkx.MultiDiGraph nx_graph: graph of the wot
        :param center: the centered node
        :param scale: a scale
        :return: the positions of the nodes
        """
        certifier_edge = [edge[0] for edge in nx_graph.in_edges() if edge[1] == center]
        certified_edge = [edge[1] for edge in nx_graph.out_edges() if edge[0] == center]

        certified = [n for n in nx_graph.nodes(data=True) if n[0] in certified_edge]

        pos = {center: (0, max(len(certified_edge),
                            len(certifier_edge))/2*0.12*scale)}

        y = 0
        x = 1 * scale
        # sort by text
        sort_certified = sorted(certified, key=lambda node_: node_[1]['attr_dict']['text'].lower())
        # add nodes and arcs
        for n in sort_certified:
            y += 0.25 * scale
            pos[n[0]] = (x, y)
        return pos

    @staticmethod
    def center_pos(nb_certifiers, nb_certified, scale):
        return 0, max(nb_certified, nb_certifiers,) / 2 * 0.12 * scale

    @staticmethod
    def certifiers_partial_layout(nx_graph, center, scale=1):
        """
        Method to generate a partial wot with certifiers layout
        :param networkx.MultiDiGraph nx_graph: graph of the wot
        :param center: the centered node
        :param scale: a scale
        :return: the positions of the nodes
        """
        certifier_edge = [edge[0] for edge in nx_graph.in_edges() if edge[1] == center]
        certified_edge = [edge[1] for edge in nx_graph.out_edges() if edge[0] == center]

        certifier = [n for n in nx_graph.nodes(data=True) if n[0] in certifier_edge]

        pos = {center: WotScene.center_pos(len(certified_edge), len(certifier_edge), scale)}

        y = 0
        x = -1 * scale
        # sort by text
        sort_certifier = sorted(certifier, key=lambda node_: node_[1]['attr_dict']['text'].lower())
        # add nodes and arcs
        for n in sort_certifier:
            y += 0.25 * scale
            pos[n[0]] = (x, y)

        return pos

    @staticmethod
    def certified_partial_layout(nx_graph, center, scale=1):
        """
        Method to generate a partial wot with certifiers layout
        :param networkx.MultiDiGraph nx_graph: graph of the wot
        :param center: the centered node
        :param scale: a scale
        :return: the positions of the nodes
        """
        certifier_edge = [edge[0] for edge in nx_graph.in_edges() if edge[1] == center]
        certified_edge = [edge[1] for edge in nx_graph.out_edges() if edge[0] == center]

        certified = [n for n in nx_graph.nodes(data=True) if n[0] in certified_edge]

        pos = {center: WotScene.center_pos(len(certified_edge), len(certifier_edge), scale)}

        y = 0
        x = 1 * scale
        # sort by text
        sort_certified = sorted(certified, key=lambda node_: node_[1]['attr_dict']['text'].lower())
        # add nodes and arcs
        for n in sort_certified:
            y += 0.25 * scale
            pos[n[0]] = (x, y)
        return pos

    @staticmethod
    def path_partial_layout(nx_graph, path, scale=1):
        """
        Layout from the center to the outside, showing the network path
        :param networkx.MultiDiGraph nx_graph: The graph to show
        :param list path:
        :param int scale:
        :return:
        """
        origin = path[0]
        certifier_edge = [edge[0] for edge in nx_graph.in_edges() if edge[1] == origin]
        certified_edge = [edge[1] for edge in nx_graph.out_edges() if edge[0] == origin]

        x, y = WotScene.center_pos(len(certified_edge), len(certifier_edge), scale)
        pos = {}

        for node in path:
            pos[node] = (x, y)
            y -= 100
        return pos

    def update_wot(self, nx_graph, identity):
        """
        draw community graph

        :param networkx.MultiDiGraph nx_graph: graph to draw
        :param sakia.core.registry.Identity identity: the wot of the identity
        """
        if identity:
            #  clear scene
            self.clear()

            certifiers_graph_pos = WotScene.certifiers_partial_layout(nx_graph, identity.pubkey, scale=200*dpi_ratio())
            certified_graph_pos = WotScene.certified_partial_layout(nx_graph, identity.pubkey, scale=200*dpi_ratio())

            # create networkx graph
            for node in nx_graph.nodes(data=True):
                if node[0] in certifiers_graph_pos:
                    v = WotNode(node, certifiers_graph_pos)
                    self.addItem(v)
                if node[0] in certified_graph_pos:
                    v = WotNode(node, certified_graph_pos)
                    self.addItem(v)

            for edge in nx_graph.edges(data=True):
                if edge[0] in certifiers_graph_pos and edge[1] == identity.pubkey:
                    self.addItem(WotEdge(edge[0], edge[1], edge[2]['attr_dict'], certifiers_graph_pos))
                if edge[0] == identity.pubkey and edge[1] in certified_graph_pos:
                    self.addItem(WotEdge(edge[0], edge[1], edge[2]['attr_dict'], certified_graph_pos))

            self.update()

    def update_path(self, nx_graph, path):
        path_graph_pos = WotScene.path_partial_layout(nx_graph, path, scale=200*dpi_ratio())
        nodes_path = [n for n in nx_graph.nodes(data=True) if n[0] in path[1:]]
        for node in nodes_path:
            v = WotNode(node, path_graph_pos)
            self.addItem(v)

        for edge in nx_graph.edges(data=True):
            if edge[0] in path_graph_pos and edge[1] in path_graph_pos:
                self.addItem(WotEdge(edge[0], edge[1], edge[2], path_graph_pos))
