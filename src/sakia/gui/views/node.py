from PyQt5.QtWidgets import QGraphicsEllipseItem, \
    QGraphicsSimpleTextItem, QMenu, QAction, QGraphicsSceneHoverEvent, \
    QGraphicsSceneContextMenuEvent

from PyQt5.QtCore import Qt, QPointF, QCoreApplication, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush, QMouseEvent, QRadialGradient
from ...core.graph.constants import NodeStatus


class Node(QGraphicsEllipseItem):
    def __init__(self, nx_node, pos, scale=1):
        """
        Create node in the graph scene

        :param tuple nx_node: Node info
        :param x_y: Position of the node
        """

        super(Node, self).__init__()

        self.metadata = nx_node[1]
        self.id = nx_node[0]
        # unpack tuple
        x, y = pos[nx_node[0]]
        x *= scale
        y *= scale
        self.status_wallet = self.metadata['status'] & NodeStatus.HIGHLIGHTED
        self.status_member = not self.metadata['status'] & NodeStatus.OUT
        self.text = self.metadata['text']
        try:
            self.setToolTip(self.metadata['tooltip'])
        except TypeError:
            raise
        self.arcs = []
        self.menu = None
        self.action_sign = None
        self.action_transaction = None
        self.action_contact = None
        self.action_show_member = None

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
        self.setPos(x, y)
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

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Right click on node to show node menu
        Except on wallet node

        :param event: scene context menu event
        """
        #  no menu on the wallet node
        if self.status_wallet:
            return None
        # create node context menus
        self.menu = QMenu()
        # action show member
        QT_TRANSLATE_NOOP('WoT.Node', 'Informations')
        self.action_show_member = QAction(QCoreApplication.translate('WoT.Node', 'Informations'), self.scene())
        self.menu.addAction(self.action_show_member)
        self.action_show_member.triggered.connect(self.member_action)
        # action add identity as contact
        QT_TRANSLATE_NOOP('WoT.Node', 'Add as contact')
        self.action_contact = QAction(QCoreApplication.translate('WoT.Node', 'Add as contact'), self.scene())
        self.menu.addAction(self.action_contact)
        self.action_contact.triggered.connect(self.contact_action)
        # action transaction toward identity
        QT_TRANSLATE_NOOP('WoT.Node', 'Send money')
        self.action_transaction = QAction(QCoreApplication.translate('WoT.Node', 'Send money'), self.scene())
        self.menu.addAction(self.action_transaction)
        self.action_transaction.triggered.connect(self.transaction_action)
        # action sign identity
        QT_TRANSLATE_NOOP('WoT.Node', 'Certify identity')
        self.action_sign = QAction(QCoreApplication.translate('WoT.Node', 'Certify identity'), self.scene())
        self.menu.addAction(self.action_sign)
        self.action_sign.triggered.connect(self.sign_action)
        # action copy identity pubkey
        QT_TRANSLATE_NOOP('WoT.Node', 'Copy pubkey')
        self.action_copy = QAction(QCoreApplication.translate('WoT.Node', 'Copy pubkey'), self.scene())
        self.menu.addAction(self.action_copy)
        self.action_copy.triggered.connect(self.copy_action)

        # run menu
        self.menu.exec(event.screenPos())

    def member_action(self):
        """
        Transaction action to identity node
        """
        # trigger scene signal
        self.scene().node_member.emit(self.id, self.metadata)

    def contact_action(self):
        """
        Transaction action to identity node
        """
        # trigger scene signal
        self.scene().node_contact.emit(self.id, self.metadata)

    def sign_action(self):
        """
        Sign identity node
        """
        # trigger scene signal
        self.scene().node_signed.emit(self.id, self.metadata)

    def copy_action(self):
        """
        Copy identity node pubkey
        """
        # trigger scene signal
        self.scene().node_copy_pubkey.emit(self.id)

    def transaction_action(self):
        """
        Transaction action to identity node
        """
        # trigger scene signal
        self.scene().node_transaction.emit(self.id, self.metadata)
