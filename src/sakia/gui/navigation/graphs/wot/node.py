from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush, QRadialGradient
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from sakia.data.graphs.constants import NodeStatus
from ..base.node import BaseNode


class WotNode(BaseNode):
    def __init__(self, nx_node, pos):
        """
        Create node in the graph scene

        :param tuple nx_node: Node info
        :param x_y: Position of the node
        """
        super().__init__(nx_node, pos)

        # color around ellipse
        outline_color = QColor('grey')
        outline_style = Qt.SolidLine
        outline_width = 1
        if self.status_wallet:
            outline_color = QColor('black')
            outline_width = 2
        if not self.status_member:
            outline_color = QColor('red')
            outline_style = Qt.SolidLine
        self.setPen(QPen(outline_color, outline_width, outline_style))

        # text inside ellipse
        self.text_item = QGraphicsSimpleTextItem(self)
        self.text_item.setText(self.text)
        text_color = QColor('grey')
        if self.status_wallet == NodeStatus.HIGHLIGHTED:
            text_color = QColor('black')
        self.text_item.setBrush(QBrush(text_color))
        # center ellipse around text
        self.setRect(
            0,
            0,
            self.text_item.boundingRect().width() * 2,
            self.text_item.boundingRect().height() * 2
        )

        #  set anchor to the center
        self.setTransform(
            QTransform().translate(-self.boundingRect().width() / 2.0, -self.boundingRect().height() / 2.0))
        # center text in ellipse
        self.text_item.setPos(self.boundingRect().width() / 4.0, self.boundingRect().height() / 4.0)

        # create gradient inside the ellipse
        gradient = QRadialGradient(QPointF(0, self.boundingRect().height() / 4), self.boundingRect().width())
        gradient.setColorAt(0, QColor('white'))
        gradient.setColorAt(1, QColor('darkgrey'))
        self.setBrush(QBrush(gradient))

        # cursor change on hover
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
