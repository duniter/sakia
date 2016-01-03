import networkx
from PyQt5.QtGui import QPainter, QWheelEvent
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush, QMouseEvent, QRadialGradient

from .node import Node
from .arc import Arc

import logging


class ExplorerView(QGraphicsView):
    def __init__(self, parent=None):
        """
        Create View to display scene

        :param parent:  [Optional, default=None] Parent widget
        """
        super().__init__(parent)

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
    node_hovered = pyqtSignal(str, name='nodeHovered')
    node_clicked = pyqtSignal(str, dict, name='nodeClicked')
    node_signed = pyqtSignal(str, dict, name='nodeSigned')
    node_transaction = pyqtSignal(str, dict, name='nodeTransaction')
    node_contact = pyqtSignal(str, dict, name='nodeContact')
    node_member = pyqtSignal(str, dict, name='nodeMember')
    node_copy_pubkey = pyqtSignal(str, name='nodeCopyPubkey')

    def __init__(self, parent=None):
        """
        Create scene of the graph

        :param parent: [Optional, default=None] Parent view
        """
        super(Scene, self).__init__(parent)

        self.lastDragPos = QPoint()
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.node_hovered.connect(self.display_path_to)

        # list of nodes in scene
        self.nodes = dict()
        self.arcs = dict()
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
        self.arcs.clear()
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
            v = Node(node, graph_pos, scale=2)
            distance = networkx.shortest_path_length(nx_graph.to_undirected(), identity.pubkey, node[0])
            factor = int((dist_max + 1) / (distance + 1) * 100)
            color = QColor('light grey').darker(factor)
            v.setBrush(QBrush(color))
            v.text_item.setBrush(QBrush(QColor('dark grey').lighter(factor)))
            self.addItem(v)
            self.nodes[node[0]] = v

        for edge in nx_graph.edges(data=True):
            edge[2]["confirmation_text"] = ""
            arc = Arc(edge[0], edge[1], edge[2], graph_pos, scale=2)
            self.addItem(arc)
            self.arcs[(edge[0], edge[1])] = arc

        self.update()

    def display_path_to(self, id):
        if id != self.identity.pubkey:
            path = networkx.shortest_path(self.nx_graph.to_undirected(), self.identity.pubkey, id)
            for arc in self.arcs.values():
                arc.paint_pen = arc.pen_from_status()
                self.update(arc.boundingRect())

            for node, next_node in zip(path[:-1], path[1:]):
                if (node, next_node) in self.arcs:
                    arc = self.arcs[(node, next_node)]
                elif (next_node, node) in self.arcs:
                    arc = self.arcs[(next_node, node)]
                if arc:
                    arc.paint_pen = QPen(QColor('black'), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    logging.debug("Update arc between {0} and {1}".format(node, next_node))
                    self.update(arc.boundingRect())
