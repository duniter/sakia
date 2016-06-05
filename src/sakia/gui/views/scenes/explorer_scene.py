import networkx
import logging
import math
from PyQt5.QtCore import QPoint, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene

from ..edges import ExplorerEdge
from ..nodes import ExplorerNode

from .base_scene import BaseScene


class ExplorerScene(BaseScene):

    node_moved = pyqtSignal(str, float, float)

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
        self.busy = None
        self.nx_graph = None
        self.identity = None
        #  axis of the scene for debug purpose
        # self.addLine(-100, 0, 100, 0)
        # self.addLine(0, -100, 0, 100)

    @staticmethod
    def _init_layout(nx_graph):
        """
        Init the data of the layout
        :param MultiGraph nx_graph:
        """
        data = {}
        INF = len(nx_graph.nodes()) * len(nx_graph.nodes())

        for node in nx_graph.nodes():
            data[node] = {
                'theta': None,
                'scenter': INF,
                'nchild': 0,
                'sparent': None,
                'stsize': 0.0,
                'span': 0.0
            }
        return data

    @staticmethod
    def _set_nstep_to_center(nx_graph, data, current):
        """
        Set the number of steps to the center
        :param networkx.MultiGraph nx_graph: the graph
        :param dict data: the data of the layout
        """
        queue = [current]
        while queue:
            n = queue.pop()
            nsteps = data[n]['scenter'] + 1
            for edge in networkx.edges(nx_graph.to_undirected(), n):
                next_node = edge[0] if edge[0] is not n else edge[1]
                if data[next_node]['sparent']:
                    continue
                if nsteps < data[next_node]['scenter']:
                    data[next_node]['scenter'] = nsteps
                    data[next_node]['sparent'] = n
                    data[n]['nchild'] += 1
                    queue.append(next_node)

    @staticmethod
    def _set_parent_nodes(nx_graph, data, center):
        """
        Set the parent of each node
        :param networkx.MultiGraph nx_graph: the graph
        :param dict data: the data of the layout
        :param str center: the id of the node at the center
        """
        unset = data[center]['scenter']
        data[center]['scenter'] = 0
        data[center]['sparent'] = None

        logging.debug("Parent node of {0}".format(center))
        ExplorerScene._set_nstep_to_center(nx_graph, data, center)
        for node in nx_graph.nodes():
            if data[node]['scenter'] == unset:
                return -1
        return max([n['scenter'] for n in data.values()])

    @staticmethod
    def _set_subtree_size(nx_graph, data):
        """
        Compute the subtree size of each node, which is the
        number of leaves in subtree rooted to the node
        :param networkx.MultiGraph nx_graph: the graph
        :param dict data:
        """
        for node in nx_graph.nodes():
            if data[node]['nchild'] > 0:
                continue
            data[node]['stsize'] += 1
            parent = data[node]['sparent']
            while parent:
                data[parent]['stsize'] += 1
                parent = data[parent]['sparent']

    @staticmethod
    def _set_subtree_spans(nx_graph, data, current):
        """
        Compute the subtree spans of each node
        :param networkx.MultiGraph nx_graph: the graph
        :param dict data: the data of the layout
        :param str current: the current node which we compute the subtree
        """
        ratio = data[current]['span'] / data[current]['stsize']
        for edge in nx_graph.to_undirected().edges(current):
            next_node = edge[0] if edge[0] != current else edge[1]
            if data[next_node]['sparent'] != current:
                continue
            if data[next_node]['span'] != 0.0:
                continue

            data[next_node]['span'] = ratio * data[next_node]['stsize']
            if data[next_node]['nchild'] > 0:
                ExplorerScene._set_subtree_spans(nx_graph, data, next_node)

    @staticmethod
    def _set_positions(nx_graph, data, current):
        """
        Compute the polar positions of each node
        :param networkx.MultiDiGraph nx_graph: the graph
        :param dict data: the data of the layout
        :param str current: the current node which we compute the subtree
        """
        if not data[current]['sparent']:
            theta = 0
        else:
            theta = data[current]['theta'] - data[current]['span'] / 2

        for edge in nx_graph.to_undirected().edges(current):
            next_node = edge[0] if edge[0] != current else edge[1]
            if data[next_node]['sparent'] != current:
                continue
            if data[next_node]['theta']:
                continue

            data[next_node]['theta'] = theta + data[next_node]['span'] / 2.0
            theta += data[next_node]['span']
            if data[next_node]['nchild'] > 0:
                ExplorerScene._set_positions(nx_graph, data, next_node)

    @staticmethod
    def twopi_layout(nx_graph, center=None):
        """
        Render the twopi layout. Ported from C code available at
        https://github.com/ellson/graphviz/blob/master/lib/twopigen/circle.c

        :param networkx.MultiDiGraph nx_graph: the networkx graph
        :param str center: the centered node
        :return:
        """
        if len(nx_graph.nodes()) == 0:
            return {}

        if len(nx_graph.nodes()) == 1:
            return {nx_graph.nodes()[0]: (0, 0)}
        #nx_graph = nx_graph.to_undirected()

        data = ExplorerScene._init_layout(nx_graph)
        if not center:
            center = networkx.center(nx_graph)[0]
        ExplorerScene._set_parent_nodes(nx_graph, data, center)
        ExplorerScene._set_subtree_size(nx_graph, data)
        data[center]['span'] = 2 * math.pi
        ExplorerScene._set_subtree_spans(nx_graph, data, center)
        data[center]['theta'] = 0.0
        ExplorerScene._set_positions(nx_graph, data, center)

        distances = networkx.shortest_path_length(nx_graph.to_undirected(), center)
        nx_pos = {}
        for node in nx_graph.nodes():
            hyp = distances[node] + 1
            theta = data[node]['theta']
            nx_pos[node] = (hyp * math.cos(theta) * 100, hyp * math.sin(theta) * 100)
        return nx_pos

    def clear(self):
        """
        clear the scene
        """
        for node in self.nodes.values():
            if node.timeline:
                node.timeline.stop()

        self.nodes.clear()
        self.edges.clear()
        super().clear()

    def update_current_identity(self, identity_pubkey):
        """
        Update the current identity loaded

        :param str identity_pubkey:
        """
        for node in self.nodes.values():
            node.stop_loading_animation()

        if identity_pubkey in self.nodes:
            self.nodes[identity_pubkey].start_loading_animation()

    def update_wot(self, nx_graph, identity, dist_max):
        """
        draw community graph

        :param networkx.Graph nx_graph: graph to draw
        :param sakia.core.registry.Identity identity: the wot of the identity
        :param dist_max: the dist_max to display
        """
        #  clear scene
        self.identity = identity
        self.nx_graph = nx_graph.copy()

        graph_pos = ExplorerScene.twopi_layout(nx_graph, center=identity.pubkey)
        if len(nx_graph.nodes()) > 0:
            distances = networkx.shortest_path_length(nx_graph.to_undirected(), identity.pubkey)
        else:
            distances = {}

        # create networkx graph
        for nx_node in nx_graph.nodes(data=True):
            if nx_node[0] in self.nodes:
                v = self.nodes[nx_node[0]]
                v.move_to(graph_pos)
            else:
                center_pos = None
                if len(nx_graph.edges(nx_node[0])) > 0:
                    for edge in nx_graph.edges(nx_node[0]):
                        neighbour = edge[0] if edge[0] != nx_node[0] else edge[1]
                        if neighbour in self.nodes:
                            center_pos = self.nodes[neighbour].pos()
                            break
                if not center_pos:
                    if identity.pubkey in self.nodes:
                        center_pos = self.nodes[identity.pubkey].pos()
                    else:
                        center_pos = QPoint(0, 0)

                v = ExplorerNode(nx_node, center_pos, graph_pos, distances[nx_node[0]], dist_max)
                self.addItem(v)
                self.nodes[nx_node[0]] = v

        for edge in nx_graph.edges(data=True):
            edge[2]["confirmation_text"] = ""
            if (edge[0], edge[1]) not in self.edges:
                distance = max(self.nodes[edge[0]].steps, self.nodes[edge[1]].steps)
                explorer_edge = ExplorerEdge(edge[0], edge[1], edge[2], graph_pos, distance, dist_max)
                self.node_moved.connect(explorer_edge.move_source_point)
                self.node_moved.connect(explorer_edge.move_destination_point)
                self.addItem(explorer_edge)
                self.edges[(edge[0], edge[1])] = explorer_edge

        self.update()

    def display_path_to(self, node_id):
        if node_id != self.identity.pubkey:
            for edge in self.edges.values():
                edge.neutralize()

            for node in self.nodes.values():
                node.neutralize()

            path = []
            try:
                path = networkx.shortest_path(self.nx_graph, node_id, self.identity.pubkey)
            except (networkx.exception.NetworkXError, networkx.exception.NetworkXNoPath) as e:
                logging.debug(str(e))
                try:
                    path = networkx.shortest_path(self.nx_graph, self.identity.pubkey, node_id)
                except (networkx.exception.NetworkXError, networkx.exception.NetworkXNoPath) as e:
                    logging.debug(str(e))

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
