from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale, QT_TRANSLATE_NOOP, QModelIndex, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from sakia.data.entities import Node
from duniterpy.documents import BMAEndpoint, SecuredBMAEndpoint, WS2PEndpoint, UnknownEndpoint
from sakia.data.processors import BlockchainProcessor
import logging


class NetworkFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.blockchain_processor = BlockchainProcessor.instanciate(app)

    def columnCount(self, parent):
        return len(NetworkTableModel.header_names)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        if left.column() == NetworkTableModel.columns_types.index('pubkey'):
            return left_data < right_data

        if left.column() == NetworkTableModel.columns_types.index('port'):
            left_data = int(left_data.split('\n')[0]) if left_data != '' else 0
            right_data = int(right_data.split('\n')[0]) if right_data != '' else 0

        if left.column() == NetworkTableModel.columns_types.index('current_block'):
            left_data = int(left_data) if left_data != '' else 0
            right_data = int(right_data) if right_data != '' else 0
            if left_data == right_data:
                hash_col = NetworkTableModel.columns_types.index('current_hash')
                return self.lessThan(self.sourceModel().index(left.row(), hash_col),
                                     self.sourceModel().index(right.row(), hash_col))

        # for every column which is not current_block or current_time,
        # if they are different from the pubkey column
        # if they are equal, we sort them by the pubkey
        if left.column() != NetworkTableModel.columns_types.index('pubkey'):
            if left_data == right_data:
                pubkey_col = NetworkTableModel.columns_types.index('pubkey')
                return self.lessThan(self.sourceModel().index(left.row(), pubkey_col),
                                     self.sourceModel().index(right.row(), pubkey_col))

        return left_data < right_data

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or section >= len(NetworkTableModel.header_names):
            return QVariant()

        _type = self.sourceModel().headerData(section, orientation, role)
        return NetworkTableModel.header_names[_type]

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_model = self.sourceModel()
        if not source_index.isValid():
            return QVariant()
        source_data = source_model.data(source_index, role)

        if role == Qt.DisplayRole:
            if index.column() == NetworkTableModel.columns_types.index('is_member'):
                value = {True: QT_TRANSLATE_NOOP("NetworkTableModel", 'yes'),
                         False: QT_TRANSLATE_NOOP("NetworkTableModel", 'no'),
                         None: QT_TRANSLATE_NOOP("NetworkTableModel", 'offline')}
                return value[source_data]

            if index.column() == NetworkTableModel.columns_types.index('pubkey'):
                return source_data[:5]

            if index.column() == NetworkTableModel.columns_types.index('current_block'):
                if source_data == -1:
                    return ""
                else:
                    return source_data

            if index.column() == NetworkTableModel.columns_types.index('address') \
                    or index.column() == NetworkTableModel.columns_types.index('port') \
                    or index.column() == NetworkTableModel.columns_types.index('api'):
                    return "<p>" + source_data.replace('\n', "<br>") + "</p>"

            if index.column() == NetworkTableModel.columns_types.index('current_hash'):
                return source_data[:10]

        if role == Qt.TextAlignmentRole:
            if source_index.column() == NetworkTableModel.columns_types.index('address') \
                    or source_index.column() == self.sourceModel().columns_types.index('current_block'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == NetworkTableModel.columns_types.index('is_member'):
                return Qt.AlignCenter

        if role == Qt.FontRole:
            is_root_col = NetworkTableModel.columns_types.index('is_root')
            index_root_col = source_model.index(source_index.row(), is_root_col)
            if source_model.data(index_root_col, Qt.DisplayRole):
                font = QFont()
                font.setBold(True)
                return font

        if role == Qt.BackgroundColorRole and self.app.parameters.dark_theme:
            return source_data.darker()

        return source_data


class NetworkTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display
    """

    header_names = {
        'address': QT_TRANSLATE_NOOP("NetworkTableModel", 'Address'),
        'port': QT_TRANSLATE_NOOP("NetworkTableModel", 'Port'),
        'api': QT_TRANSLATE_NOOP('NetworkTableModel', 'API'),
        'current_block': QT_TRANSLATE_NOOP("NetworkTableModel", 'Block'),
        'current_hash': QT_TRANSLATE_NOOP("NetworkTableModel", 'Hash'),
        'uid': QT_TRANSLATE_NOOP("NetworkTableModel", 'UID'),
        'is_member': QT_TRANSLATE_NOOP("NetworkTableModel", 'Member'),
        'pubkey': QT_TRANSLATE_NOOP("NetworkTableModel", 'Pubkey'),
        'software': QT_TRANSLATE_NOOP("NetworkTableModel", 'Software'),
        'version': QT_TRANSLATE_NOOP("NetworkTableModel", 'Version')
    }
    columns_types = (
        'address',
        'port',
        'api',
        'current_block',
        'current_hash',
        'uid',
        'is_member',
        'pubkey',
        'software',
        'version',
        'is_root',
        'state',
        'node'
    )

    ONLINE = 0
    OFFLINE = 1
    DESYNCED = 3

    node_colors = {
        ONLINE: QColor('#99ff99'),
        OFFLINE: QColor('#ff9999'),
        DESYNCED: QColor('#ffbd81')
    }

    node_icons = {
        ONLINE: ":/icons/synchronized",
        OFFLINE: ":/icons/offline",
        DESYNCED: ":/icons/forked"
    }
    node_states = {
        ONLINE: lambda: QT_TRANSLATE_NOOP("NetworkTableModel", 'Online'),
        OFFLINE: lambda: QT_TRANSLATE_NOOP("NetworkTableModel", 'Offline'),
        DESYNCED: lambda: QT_TRANSLATE_NOOP("NetworkTableModel", 'Unsynchronized')
    }
    
    def __init__(self, network_service, parent=None):
        """
        The table showing nodes
        :param sakia.services.NetworkService network_service:
        :param parent:
        """
        super().__init__(parent)
        self.network_service = network_service
        
        self.nodes_data = []
        self.network_service.node_changed.connect(self.change_node)
        self.network_service.node_removed.connect(self.remove_node)
        self.network_service.new_node_found.connect(self.add_node)
        self.network_service.latest_block_changed.connect(self.init_nodes)
        self._logger = logging.getLogger('sakia')

    def data_node(self, node: Node, current_buid=None) -> tuple:
        """
        Return node data tuple
        :param ..core.net.node.Node node: Network node
        :return:
        """

        addresses = []
        ports = []
        api_list = []
        for e in node.endpoints:

            if isinstance(e, UnknownEndpoint):
                api_list.append(e.api)
            else:
                api_list.append(type(e).API)

            if isinstance(e, BMAEndpoint) or isinstance(e, SecuredBMAEndpoint):
                if e.server:
                    addresses.append(e.server)
                elif e.ipv6:
                    addresses.append(e.ipv6)
                elif e.ipv4:
                    addresses.append(e.ipv4)
                ports.append(str(e.port))
            elif isinstance(e, WS2PEndpoint):
                addresses.append(e.server + " [" + e.ws2pid + "]")
                ports.append(str(e.port))
            elif isinstance(e, UnknownEndpoint):
                addresses.append(" ".join(e.properties))
                ports.append("-")
            else:
                addresses.append(e.server)
                ports.append(str(e.port))

        address = "\n".join(addresses)
        port = "\n".join(ports)
        api = "\n".join(api_list)

        if node.current_buid:
            number, block_hash = node.current_buid.number, node.current_buid.sha_hash
        else:
            number, block_hash = "", ""
        state = node.state
        if not current_buid:
            current_buid = self.network_service.current_buid()
        if node.online():
            state = NetworkTableModel.ONLINE
        else:
            state = NetworkTableModel.OFFLINE
        if node.online() and node.current_buid != current_buid:
            state = NetworkTableModel.DESYNCED

        return (address, port, api, number, block_hash, node.uid,
                node.member, node.pubkey, node.software, node.version, node.root, state,
                node)

    def init_nodes(self, current_buid=None):
        self._logger.debug("Init nodes table")
        self.beginResetModel()
        self.nodes_data = []
        nodes_data = []
        for node in self.network_service.nodes():
            data = self.data_node(node, current_buid)
            nodes_data.append(data)
        self.nodes_data = nodes_data
        self.endResetModel()

    def add_node(self, node):
        self.beginInsertRows(QModelIndex(), len(self.nodes_data), len(self.nodes_data))
        self.nodes_data.append(self.data_node(node))
        self.endInsertRows()

    def change_node(self, node):
        for i, n in enumerate(self.nodes_data):
            if n[NetworkTableModel.columns_types.index('pubkey')] == node.pubkey:
                self.nodes_data[i] = self.data_node(node)
                self.dataChanged.emit(self.index(i, 0), self.index(i, len(self.columns_types)-1))
                return

    def remove_node(self, node):
        for i, n in enumerate(self.nodes_data.copy()):
            if n[NetworkTableModel.columns_types.index('pubkey')] == node.pubkey:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.nodes_data.pop(i)
                self.endRemoveRows()
                return

    def rowCount(self, parent):
        return len(self.nodes_data)

    def columnCount(self, parent):
        return len(NetworkTableModel.columns_types)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        return NetworkTableModel.columns_types[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        node = self.nodes_data[row]
        if role == Qt.DisplayRole:
            return node[col]
        if role == Qt.BackgroundColorRole:
            return NetworkTableModel.node_colors[node[NetworkTableModel.columns_types.index('state')]]

        if role == Qt.ToolTipRole:
            return NetworkTableModel.node_states[node[NetworkTableModel.columns_types.index('state')]]()

        if role == Qt.DecorationRole and index.column() == 0:
            return QIcon(NetworkTableModel.node_icons[node[NetworkTableModel.columns_types.index('state')]])

        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

