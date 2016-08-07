from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QWheelEvent
from PyQt5.QtWidgets import QGraphicsView
from .scene import WotScene


class WotGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        """
        Create View to display scene

        :param parent:  [Optional, default=None] Parent widget
        """
        super().__init__(parent)

        self.setScene(WotScene(self))

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
            super().wheelEvent(event)