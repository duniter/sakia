import networkx
from PyQt5.QtGui import QPainter, QWheelEvent
from PyQt5.QtCore import Qt, QPoint,  pyqtSignal
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene

from .node import Node
from .arc import Arc

class WotView(QGraphicsView):
    def __init__(self, parent=None):
        """
        Create View to display scene

        :param parent:  [Optional, default=None] Parent widget
        """
        super(WotView, self).__init__(parent)

        self.setScene(Scene(self))

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

    def wheelEvent(self, event: QWheelEvent):
        """
        Zoom in/out on the mouse cursor
        """
        # zoom only when CTRL key pressed
        if (event.modifiers() & Qt.ControlModifier) == Qt.ControlModifier:
            steps = event.angleDelta().y() / 15 / 8

            if steps == 0:
                event.ignore()
                return

            # scale factor 1.25
            sc = pow(1.25, steps)
            self.scale(sc, sc)
            self.centerOn(self.mapToScene(event.pos()))
            event.accept()
        #  act normally on scrollbar
        else:
            # transmit event to parent class wheelevent
            super(QGraphicsView, self).wheelEvent(event)


class Scene(QGraphicsScene):
    # This defines signals taking string arguments
    node_clicked = pyqtSignal(str, dict, name='nodeClicked')
    node_signed = pyqtSignal(str, dict, name='nodeSigned')
    node_transaction = pyqtSignal(str, dict, name='nodeTransaction')
    node_contact = pyqtSignal(str, dict, name='nodeContact')
    node_member = pyqtSignal(str, dict, name='nodeMember')
    node_copy_pubkey = pyqtSignal(str, name='nodeCopyPubkey')
    node_hovered = pyqtSignal(str, name='nodeHovered')

    def __init__(self, parent=None):
        """
        Create scene of the graph

        :param parent: [Optional, default=None] Parent view
        """
        super(Scene, self).__init__(parent)

        self.lastDragPos = QPoint()
        self.setItemIndexMethod(QGraphicsScene.NoIndex)

        # list of nodes in scene
        self.nodes = dict()
        #  axis of the scene for debug purpose
        # self.addLine(-100, 0, 100, 0)
        # self.addLine(0, -100, 0, 100)

    def certified_partial_layout(self, nx_graph, center, scale=1):
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
        sort_certified = sorted(certified, key=lambda node_: node_[1]['text'].lower())
        # add nodes and arcs
        for n in sort_certified:
            y += 0.25 * scale
            pos[n[0]] = (x, y)
        return pos

    def certifiers_partial_layout(self, nx_graph, center, scale=1):
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

        pos = {center: (0, max(len(certified_edge),
                                    len(certifier_edge))/2*0.12*scale)}

        y = 0
        x = -1 * scale
        # sort by text
        sort_certifier = sorted(certifier, key=lambda node_: node_[1]['text'].lower())
        # add nodes and arcs
        for n in sort_certifier:
            y += 0.25 * scale
            pos[n[0]] = (x, y)

        return pos

    def certified_partial_layout(self, nx_graph, center, scale=1):
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
        sort_certified = sorted(certified, key=lambda node_: node_[1]['text'].lower())
        # add nodes and arcs
        for n in sort_certified:
            y += 0.25 * scale
            pos[n[0]] = (x, y)
        return pos

    def path_partial_layout(self, nx_graph, path, scale=1):
        """

        :param networkx.Graph nx_graph: The graph to show
        :param list path:
        :param int scale:
        :return:
        """
        destination = path[-1]
        certifier_edge = [edge[0] for edge in nx_graph.in_edges() if edge[1] == destination]
        certified_edge = [edge[1] for edge in nx_graph.out_edges() if edge[0] == destination]

        x = 0
        y = max(len(certified_edge), len(certifier_edge))/2*0.12*scale
        pos = {destination: (x, y)}

        for node in reversed(path[:-1]):
            y -= 100
            pos[node] = (x, y)
        return pos

    def update_wot(self, nx_graph, identity):
        """
        draw community graph

        :param networkx.Graph nx_graph: graph to draw
        :param sakia.core.registry.Identity identity: the wot of the identity
        """
        #  clear scene
        self.clear()
        certifiers_graph_pos = self.certifiers_partial_layout(nx_graph, identity.pubkey, scale=200)
        certified_graph_pos = self.certified_partial_layout(nx_graph, identity.pubkey, scale=200)

        # create networkx graph
        for node in nx_graph.nodes(data=True):
            if node[0] in certifiers_graph_pos:
                v = Node(node, certifiers_graph_pos)
                self.addItem(v)
            if node[0] in certified_graph_pos:
                v = Node(node, certified_graph_pos)
                self.addItem(v)

        for edge in nx_graph.edges(data=True):
            if edge[0] in certifiers_graph_pos and edge[1] == identity.pubkey:
                self.addItem(Arc(edge[0], edge[1], edge[2], certifiers_graph_pos))
            if edge[0] == identity.pubkey and edge[1] in certified_graph_pos:
                self.addItem(Arc(edge[0], edge[1], edge[2], certified_graph_pos))

        self.update()

    def update_path(self, nx_graph, path):
        path_graph_pos = self.path_partial_layout(nx_graph, path, scale=200)
        nodes_path = [n for n in nx_graph.nodes(data=True) if n[0] in path[:-1]]
        for node in nodes_path:
            v = Node(node, path_graph_pos)
            self.addItem(v)

        for edge in nx_graph.edges(data=True):
            if edge[0] in path_graph_pos and edge[1] in path_graph_pos:
                self.addItem(Arc(edge[0], edge[1], edge[2], path_graph_pos))
