from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene


class BaseScene(QGraphicsScene):
    # This defines signals taking string arguments
    node_clicked = pyqtSignal(str, dict)
    node_signed = pyqtSignal(str, dict)
    node_transaction = pyqtSignal(str, dict)
    node_contact = pyqtSignal(str, dict)
    node_member = pyqtSignal(str, dict)
    node_copy_pubkey = pyqtSignal(str)
    node_hovered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)