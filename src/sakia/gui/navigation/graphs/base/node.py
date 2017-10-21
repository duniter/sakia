from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneContextMenuEvent

from sakia.data.graphs.constants import NodeStatus


class BaseNode(QGraphicsEllipseItem):
    def __init__(self, nx_node, pos):
        """
        Create node in the graph scene

        :param tuple nx_node: Node info
        :param x_y: Position of the node
        """

        super().__init__()

        self.metadata = nx_node[1]['attr_dict']
        self.id = nx_node[0]
        # unpack tuple
        x, y = pos[nx_node[0]]
        self.setPos(x, y)
        self.status_wallet = self.metadata['status'] & NodeStatus.HIGHLIGHTED
        self.status_member = not self.metadata['status'] & NodeStatus.OUT
        self.text = self.metadata['text']
        self.setToolTip(self.text + " - " + self.metadata['tooltip'])
        self.arcs = []
        self.menu = None
        self.action_sign = None
        self.action_transaction = None
        self.action_contact = None
        self.action_show_member = None

    def update_metadata(self, metadata):
        self.metadata = metadata
        self.status_wallet = self.metadata['status'] & NodeStatus.HIGHLIGHTED
        self.status_member = not self.metadata['status'] & NodeStatus.OUT
        self.text = self.metadata['text']
        self.setToolTip(self.text + " - " + self.metadata['tooltip'])

    def mousePressEvent(self, event: QMouseEvent):
        """
        Click on mouse button

        :param event: mouse event
        """
        if event.button() == Qt.LeftButton:
            # trigger scene signal
            self.scene().node_clicked.emit(self.id, self.metadata)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Mouse enter on node zone

        :param event: scene hover event
        """
        self.setCursor(Qt.ArrowCursor)
        self.scene().node_hovered.emit(self.id)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Right click on node to show node menu
        Except on wallet node

        :param event: scene context menu event
        """
        self.scene().node_context_menu_requested.emit(self.metadata['identity'])

