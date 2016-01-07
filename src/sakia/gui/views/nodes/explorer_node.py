from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush, QRadialGradient
from ....core.graph.constants import NodeStatus
from .base_node import BaseNode
import logging


class ExplorerNode(BaseNode):
    def __init__(self, nx_node, pos, steps, steps_max):
        """
        Create node in the graph scene

        :param tuple nx_node: Node info
        :param x_y: Position of the node
        :param int steps: The steps from the center identity
        :param int steps_max: The steps max of the graph
        """
        super().__init__(nx_node, pos)

        self.x *= 2
        self.y *= 2
        self.steps = steps
        self.steps_max = steps_max
        self.highlighted = False

        # text inside ellipse
        self.text_item = QGraphicsSimpleTextItem(self)
        self.text_item.setText(self.text)
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
        self.setPos(self.x, self.y)
        # center text in ellipse
        self.text_item.setPos(self.boundingRect().width() / 4.0, self.boundingRect().height() / 4.0)

        # cursor change on hover
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

        self._refresh_colors()

    def _refresh_colors(self):
        """
        Refresh elements in the node
        """
        # color around ellipse
        outline_color = QColor('black')
        outline_style = Qt.SolidLine
        outline_width = 1
        if self.status_wallet:
            outline_color = QColor('grey')
            outline_width = 2
        if not self.status_member:
            outline_color = QColor('red')
            outline_style = Qt.SolidLine
        self.setPen(QPen(outline_color, outline_width, outline_style))

        if self.highlighted:
            text_color = QColor('grey')
        else:
            text_color = QColor('black')

        if self.status_wallet == NodeStatus.HIGHLIGHTED:
            text_color = QColor('grey')
        self.text_item.setBrush(QBrush(text_color))

        # create gradient inside the ellipse
        gradient = QRadialGradient(QPointF(0, self.boundingRect().height() / 4), self.boundingRect().width())
        color = QColor()
        color.setHsv(120 - 60 / self.steps_max * self.steps,
                     180 + 50 / self.steps_max * self.steps,
                     60 + 170 / self.steps_max * self.steps)
        if self.highlighted:
            color = color.darker(200)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, color.darker(150))
        self.setBrush(QBrush(gradient))

    def highlight(self):
        """
        Highlight the edge in the scene
        """
        self.highlighted = True
        self._refresh_colors()
        self.update(self.boundingRect())

    def neutralize(self):
        """
        Neutralize the edge in the scene
        """
        self.highlighted = False
        self._refresh_colors()
        self.update(self.boundingRect())
