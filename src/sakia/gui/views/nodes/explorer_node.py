from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt, QPointF, QTimeLine, QTimer
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush, QRadialGradient
from ....core.graph.constants import NodeStatus
from .base_node import BaseNode
import math


class ExplorerNode(BaseNode):
    def __init__(self, nx_node, center_pos, nx_pos, steps, steps_max):
        """
        Create node in the graph scene

        :param tuple nx_node: Node info
        :param center_pos: The position of the center node
        :param nx_pos: Position of the nodes in the graph
        :param int steps: The steps from the center identity
        :param int steps_max: The steps max of the graph
        """
        super().__init__(nx_node, nx_pos)

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
        # center text in ellipse
        self.text_item.setPos(self.boundingRect().width() / 4.0, self.boundingRect().height() / 4.0)

        # cursor change on hover
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

        # animation and moves
        self.timeline = None
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.next_tick)
        self.loading_counter = 0
        self._refresh_colors()
        self.setPos(center_pos)
        self.move_to(nx_pos)

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
        color = color.lighter(math.fabs(math.sin(self.loading_counter / 100 * math.pi) * 100) + 100)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, color.darker(150))
        self.setBrush(QBrush(gradient))

    def move_to(self, nx_pos):
        """
        Move to corresponding position
        :param nx_pos:
        :return:
        """
        origin_x = self.x()
        origin_y = self.y()
        final_x = nx_pos[self.id][0]
        final_y = nx_pos[self.id][1]

        def frame_move(frame):
            value = self.timeline.valueForTime(self.timeline.currentTime())
            x = origin_x + (final_x - origin_x) * value
            y = origin_y + (final_y - origin_y) * value
            self.setPos(x, y)
            self.scene().node_moved.emit(self.id, x, y)

        def timeline_ends():
            self.setPos(final_x, final_y)
            self.timeline = None

        # Remember to hold the references to QTimeLine and QGraphicsItemAnimation instances.
        # They are not kept anywhere, even if you invoke QTimeLine.start().
        self.timeline = QTimeLine(1000)
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(frame_move)
        self.timeline.finished.connect(timeline_ends)

        self.timeline.start()

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

    def start_loading_animation(self):
        """
        Neutralize the edge in the scene
        """
        if not self.loading_timer.isActive():
            self.loading_timer.start(10)

    def stop_loading_animation(self):
        """
        Neutralize the edge in the scene
        """
        self.loading_timer.stop()
        self.loading_counter = 100
        self._refresh_colors()
        self.update(self.boundingRect())

    def next_tick(self):
        """
        Next tick
        :return:
        """
        self.loading_counter += 1
        self.loading_counter %= 100
        self._refresh_colors()
        self.update(self.boundingRect())

