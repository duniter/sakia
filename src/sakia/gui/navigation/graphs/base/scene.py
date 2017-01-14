from sakia.data.entities import Identity
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsSceneContextMenuEvent


class BaseScene(QGraphicsScene):
    # This defines signals taking string arguments
    node_context_menu_requested = pyqtSignal(Identity)
    node_hovered = pyqtSignal(str)
    node_clicked = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
