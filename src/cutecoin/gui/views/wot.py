# -*- coding: utf-8 -*-

import math
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QColor, QRadialGradient,\
    QPainterPath, QMouseEvent, QWheelEvent, QTransform
from PyQt5.QtCore import Qt, QRectF, QLineF, QPoint, QPointF, QSizeF, qFuzzyCompare, pyqtSignal
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,\
    QGraphicsSimpleTextItem, QGraphicsLineItem, QMenu, QAction, QGraphicsSceneHoverEvent,\
    QGraphicsSceneContextMenuEvent

NODE_STATUS_HIGHLIGHTED = 1
NODE_STATUS_SELECTED = 2
ARC_STATUS_STRONG = 1
ARC_STATUS_WEAK = 2


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
        # act normally on scrollbar
        else:
            # transmit event to parent class wheelevent
            super(QGraphicsView, self).wheelEvent(event)


class Scene(QGraphicsScene):

    # This defines signals taking string arguments
    node_clicked = pyqtSignal(str, name='nodeClicked')
    node_signed = pyqtSignal(dict, name='nodeSigned')
    node_transaction = pyqtSignal(dict, name='nodeTransaction')
    node_contact = pyqtSignal(dict, name='nodeContact')

    def __init__(self, parent=None):
        """
        Create scene of the graph

        :param parent: [Optional, default=None] Parent view
        """
        super(Scene, self).__init__(parent)

        self.lastDragPos = QPoint()
        self.setItemIndexMethod(QGraphicsScene.NoIndex)

        # axis of the scene for debug purpose
        # self.addLine(-100, 0, 100, 0)
        # self.addLine(0, -100, 0, 100)

    def add_node(self, metadata, pos):
        """
        Add a node item in the graph

        :param dict metadata: Node metadata
        :param tuple pos: Position (x,y) of the node

        :return: Node
        """
        node = Node(metadata, pos)
        self.addItem(node)
        return node

    def add_arc(self, source_node, destination_node, metadata):
        """
        Add an arc between two nodes

        :param Node source_node: Source node of the arc
        :param Node destination_node: Destination node of the arc
        :param dict arc: Arc data

        :return: Arc
        """
        arc = Arc(source_node, destination_node, metadata)
        self.addItem(arc)
        return arc

    def update_wot(self, graph):
        """
        draw community graph

        :param dict graph: graph to draw
        """
        # clear scene
        self.clear()

        # capture selected node (to draw it in the center)
        for _id, node in graph.items():
            if node['status'] & NODE_STATUS_SELECTED:
                selected_id = _id
                selected_node = node

        root_node = self.add_node(selected_node, (0, 0))

        # add certified by selected node
        y = 0
        x = 200
        # capture nodes for sorting by text
        nodes = list()
        for arc in selected_node['arcs']:
            nodes.append({'node': graph[arc['id']], 'arc': arc})
        # sort by text
        nodes = sorted(nodes, key=lambda _node: _node['node']['text'].lower())
        # add nodes and arcs
        for _node in nodes:
            node = self.add_node(_node['node'], (x, y))
            self.add_arc(root_node, node, _node['arc'])
            y += 50

        # add certifiers of selected node
        y = 0
        x = -200
        # sort by text
        nodes = ((k, v) for (k, v) in sorted(graph.items(), key=lambda kv: kv[1]['text'].lower()) if selected_id in (arc['id'] for arc in v['arcs']))
        # add nodes and arcs
        for _id, certifier_node in nodes:
            node = self.add_node(certifier_node, (x, y))
            for arc in certifier_node['arcs']:
                if arc['id'] == selected_id:
                    self.add_arc(node, root_node, arc)
            y += 50

        self.update()


class Node(QGraphicsEllipseItem):
    def __init__(self, metadata, x_y):
        """
        Create node in the graph scene

        :param dict metadata: Node metadata
        :param x_y: Position of the node
        """
        # unpack tuple
        x, y = x_y

        super(Node, self).__init__()

        self.metadata = metadata
        self.status_wallet = self.metadata['status'] & NODE_STATUS_HIGHLIGHTED
        self.text = self.metadata['text']
        self.setToolTip(self.metadata['tooltip'])
        self.arcs = []
        self.menu = None
        self.action_sign = None
        self.action_transaction = None
        self.action_contact = None

        # color around ellipse
        outline_color = QColor('grey')
        if self.status_wallet:
            outline_color = QColor('black')
        self.setPen(QPen(outline_color))

        # text inside ellipse
        self.text_item = QGraphicsSimpleTextItem(self)
        self.text_item.setText(self.text)
        text_color = QColor('grey')
        if self.status_wallet == NODE_STATUS_HIGHLIGHTED:
            text_color = QColor('black')
        self.text_item.setBrush(QBrush(text_color))
        # center ellipse around text
        self.setRect(
            0,
            0,
            self.text_item.boundingRect().width() * 2,
            self.text_item.boundingRect().height() * 2
        )

        # set anchor to the center
        self.setTransform(QTransform().translate(-self.boundingRect().width()/2.0, -self.boundingRect().height()/2.0))
        self.setPos(x, y)
        #print(x, y)
        # center text in ellipse
        self.text_item.setPos(self.boundingRect().width() / 4.0, self.boundingRect().height() / 4.0)

        # create gradient inside the ellipse
        gradient = QRadialGradient(QPointF(0, self.boundingRect().height() / 4), self.boundingRect().width())
        gradient.setColorAt(0, QColor('white'))
        gradient.setColorAt(1, QColor('darkgrey'))
        self.setBrush(QBrush(gradient))

        # cursor change on hover
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Click on mouse button

        :param event: mouse event
        """
        if event.button() == Qt.LeftButton:
            # trigger scene signal
            self.scene().node_clicked.emit(self.metadata['id'])

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Mouse enter on node zone

        :param event: scene hover event
        """
        self.setCursor(Qt.ArrowCursor)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Right click on node to show node menu

        :param event: scene context menu event
        """
        # create node context menus
        self.menu = QMenu()
        # action add identity as contact
        self.action_contact = QAction('Add as contact', self.scene())
        self.menu.addAction(self.action_contact)
        self.action_contact.triggered.connect(self.contact_action)
        # action transaction toward identity
        self.action_transaction = QAction('Send money', self.scene())
        self.menu.addAction(self.action_transaction)
        self.action_transaction.triggered.connect(self.transaction_action)
        # action sign identity
        self.action_sign = QAction('Certify identity', self.scene())
        self.menu.addAction(self.action_sign)
        self.action_sign.triggered.connect(self.sign_action)
        # run menu
        self.menu.exec(event.screenPos())

    def add_arc(self, arc):
        """
        Add arc to the arc list

        :param arc: Arc
        """
        self.arcs.append(arc)

    def sign_action(self):
        """
        Sign identity node
        """
        # trigger scene signal
        self.scene().node_signed.emit(self.metadata)

    def transaction_action(self):
        """
        Transaction action to identity node
        """
        # trigger scene signal
        self.scene().node_transaction.emit(self.metadata)

    def contact_action(self):
        """
        Transaction action to identity node
        """
        # trigger scene signal
        self.scene().node_contact.emit(self.metadata)

class Arc(QGraphicsLineItem):
    def __init__(self, source_node, destination_node, metadata):
        """
        Create an arc between two nodes

        :param Node source_node: Source node of the arc
        :param Node destination_node: Destination node of the arc
        :param dict metadata: Arc metadata
        """
        super(Arc, self).__init__()

        self.metadata = metadata
        self.source = source_node
        self.destination = destination_node
        self.setToolTip(self.metadata['tooltip'])
        self.source.add_arc(self)

        self.status = self.metadata['status']

        self.source_point = None
        self.destination_point = None
        self.arrow_size = 5.0

        self.setAcceptedMouseButtons(Qt.NoButton)

        # cursor change on hover
        self.setAcceptHoverEvents(True)
        self.adjust()
        self.setZValue(0)

    def adjust(self):
        """
        Draw the arc line
        """
        if not self.source or not self.destination:
            return
        line = QLineF(
            self.mapFromItem(
                self.source,
                self.source.boundingRect().width() - (self.source.boundingRect().width() / 2.0),
                self.source.boundingRect().height() / 2.0
            ),
            self.mapFromItem(
                self.destination,
                self.destination.boundingRect().width() / 2.0,
                self.destination.boundingRect().height() / 2.0
            )
        )
        self.prepareGeometryChange()
        self.source_point = line.p1()
        self.destination_point = line.p2()

        # mouse over on line only
        self.setLine(line)

    # virtual function require subclassing
    def boundingRect(self):
        """
        Return the bounding rectangle size

        :return: QRectF
        """
        if not self.source or not self.destination:
            return QRectF()
        pen_width = 1.0
        extra = (pen_width + self.arrow_size) / 2.0

        return QRectF(
            self.source_point, QSizeF(
                self.destination_point.x() - self.source_point.x(),
                self.destination_point.y() - self.source_point.y()
            )
        ).normalized().adjusted(
            -extra,
            -extra,
            extra,
            extra
        )

    def paint(self, painter, option, widget):
        """
        Customize line adding an arrow head

        :param QPainter painter: Painter instance of the item
        :param option:  Painter option of the item
        :param widget:  Widget instance
        """
        if not self.source or not self.destination:
            return
        line = QLineF(self.source_point, self.destination_point)
        if qFuzzyCompare(line.length(), 0):
            return

        # Draw the line itself
        color = QColor()
        style = Qt.SolidLine
        if self.status == ARC_STATUS_STRONG:
            color.setNamedColor('blue')
        if self.status == ARC_STATUS_WEAK:
            color.setNamedColor('salmon')
            style = Qt.DashLine

        painter.setPen(QPen(color, 1, style, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)
        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        # Draw the arrows
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (2.0 * math.pi) - angle

        # arrow in the middle of the arc
        hpx = (line.p2().x() + line.p1().x()) / 2.0
        hpy = (line.p2().y() - line.p1().y()) / 2.0
        if line.dy() < 0:
            hpy = -hpy
        head_point = QPointF(hpx, hpy)

        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        destination_arrow_p1 = head_point + QPointF(
            math.sin(angle - math.pi / 3) * self.arrow_size,
            math.cos(angle - math.pi / 3) * self.arrow_size)
        destination_arrow_p2 = head_point + QPointF(
            math.sin(angle - math.pi + math.pi / 3) * self.arrow_size,
            math.cos(angle - math.pi + math.pi / 3) * self.arrow_size)

        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([head_point, destination_arrow_p1, destination_arrow_p2]))

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Mouse enter on arc zone

        :param event: scene hover event
        """
        self.setCursor(Qt.ArrowCursor)

    def shape(self):
        """
        Return real shape of the item to detect collision or hover accurately

        :return: QPainterPath
        """
        # detection mouse hover on arc path
        path = QPainterPath()
        path.addPolygon(QPolygonF([self.line().p1(), self.line().p2()]))
        # add handles at the start and end of arc
        path.addRect(QRectF(
            self.line().p1().x()-5,
            self.line().p1().y()-5,
            self.line().p1().x()+5,
            self.line().p1().y()+5
        ))
        path.addRect(QRectF(
            self.line().p2().x()-5,
            self.line().p2().y()-5,
            self.line().p2().x()+5,
            self.line().p2().y()+5
        ))
        return path
