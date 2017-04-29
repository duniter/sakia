from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QSize
from PyQt5.QtGui import QIcon, QTextDocument
import logging


def parse_node(node_data, parent_item):
    node = NodeItem(node_data, parent_item)
    if parent_item:
        parent_item.appendChild(node)
    if 'children' in node_data:
        for child in node_data['children']:
            parse_node(child, node)
    return node


class NodeItem(QAbstractItemModel):
    def __init__(self, node, parent_item):
        super().__init__(parent_item)
        self.children = []
        self.node = node
        self.parent_item = parent_item

    def appendChild(self, node_item):
        self.children.append(node_item)

    def child(self, row):
        return self.children[row]

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return 1

    def data(self, index, role):
        if role == Qt.DisplayRole and 'title' in self.node:
            return self.node['title']

        if role == Qt.ToolTipRole and 'tooltip' in self.node:
            return self.node['tooltip']

        if role == Qt.DecorationRole and 'icon' in self.node:
            return QIcon(self.node['icon'])

        if role == Qt.SizeHintRole:
            return QSize(1, 22)

        if role == GenericTreeModel.ROLE_RAW_DATA:
            return self.node

    def row(self):
        if self.parent_item:
            return self.parent_item.row() + self.parent_item.children.index(self)
        return 0

    def column(self):
        return 0


class GenericTreeModel(QAbstractItemModel):

    """
    A Qt abstract item model to display nodes from a dict


    dict_format = {
        'root_node': {
            'node': ["title", "icon", "tooltip", "action"],
            'children': {}
        }
    }

    """

    ROLE_RAW_DATA = 101

    def __init__(self, title, root_item):
        """
        Constructor
        """
        super().__init__(None)
        self.title = title
        self.root_item = root_item

    @classmethod
    def create(cls, title, data):
        root_item = NodeItem({}, None)
        for node in data:
            parse_node(node, root_item)

        return cls(title, root_item)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role in (Qt.DisplayRole,
                    Qt.DecorationRole,
                    Qt.ToolTipRole,
                    Qt.SizeHintRole,
                    GenericTreeModel.ROLE_RAW_DATA) \
            and index.column() == 0:
            return item.data(0, role)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal \
        and role == Qt.DisplayRole and section == 0:
            return self.title
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent_index):
        if not parent_index.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent_index.internalPointer()

        if parent_index.column() > 0:
            return 0

        return parent_item.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0:
            return True

    def insert_node(self, raw_data):
        self.beginInsertRows(QModelIndex(), self.rowCount(QModelIndex()), 0)
        parse_node(raw_data, self.root_item)
        self.endInsertRows()
