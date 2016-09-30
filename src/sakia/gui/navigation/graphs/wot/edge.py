import math

from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QSizeF, \
                        qFuzzyCompare
from PyQt5.QtGui import QColor, QPen, QPolygonF

from sakia.data.graphs.constants import EdgeStatus
from ..base.edge import BaseEdge


class WotEdge(BaseEdge):
    def __init__(self, source_node, destination_node, metadata, pos):
        """
        Create an arc between two nodes

        :param Node source_node: Source node of the arc
        :param Node destination_node: Destination node of the arc
        :param dict metadata: Arc metadata
        """
        super().__init__(source_node, destination_node, metadata, pos)

        self.arrow_size = 5
        #  cursor change on hover
        self.setAcceptHoverEvents(True)
        self.setZValue(0)
        self._colors = {
            EdgeStatus.STRONG: 'blue',
            EdgeStatus.WEAK: 'salmon'
        }
        self._line_styles = {
            EdgeStatus.STRONG: Qt.SolidLine,
            EdgeStatus.WEAK: Qt.DashLine
        }

    @property
    def color_name(self):
        return self._colors[self.status]

    @property
    def line_style(self):
        return self._line_styles[self.status]

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
        color.setNamedColor(self.color_name)
        style = self.line_style

        painter.setPen(QPen(color, 1, style, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)
        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        # Draw the arrows
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (2.0 * math.pi) - angle

        #  arrow in the middle of the arc
        hpx = line.p1().x() + (line.dx() / 2.0)
        hpy = line.p1().y() + (line.dy() / 2.0)
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

        if self.metadata["confirmation_text"]:
            painter.drawText(head_point, self.metadata["confirmation_text"])
