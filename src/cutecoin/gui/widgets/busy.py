from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt

import math


class Busy(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.timer = None

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(12):
            if self.counter % 12 == i:
                painter.setBrush(QBrush(QColor(165, 165, 165, (self.counter % 12)*22)))
            else:
                painter.setBrush(QBrush(QColor(165, 165, 165)))
            painter.drawEllipse(
                self.width()/2 + 50 * math.cos(2 * math.pi * i / 12.0) - 5,
                self.height()/2 + 50 * math.sin(2 * math.pi * i / 12.0) - 5,
                12, 12)

        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(150)
        self.counter = 0
        super().showEvent(event)

    def hideEvent(self, event):
        if self.timer:
            self.killTimer(self.timer)
            self.timer = None
        super().hideEvent(event)

    def timerEvent(self, event):
        self.counter += 1
        self.update()
        super().timerEvent(event)
