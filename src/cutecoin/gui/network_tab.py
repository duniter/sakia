"""
Created on 20 févr. 2015

@author: inso
"""

import logging
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QModelIndex, pyqtSlot
from ..models.network import NetworkTableModel, NetworkFilterProxyModel
from ..gen_resources.network_tab_uic import Ui_NetworkTabWidget


class NetworkTabWidget(QWidget, Ui_NetworkTabWidget):
    """
    classdocs
    """

    def __init__(self, community):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        model = NetworkTableModel(community)
        proxy = NetworkFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.table_network.setModel(proxy)
        self.table_network.sortByColumn(0, Qt.DescendingOrder)
        self.table_network.resizeColumnsToContents()
        community.network.nodes_changed.connect(self.refresh_nodes)
        self.community = community

    @pyqtSlot()
    def refresh_nodes(self):
        logging.debug("Refresh nodes")
        self.table_network.model().sourceModel().modelReset.emit()

    def node_context_menu(self, point):
            index = self.table_network.indexAt(point)
            model = self.table_network.model()
            if index.row() < model.rowCount(QModelIndex()):
                source_index = model.mapToSource(index)
                is_root_col = model.sourceModel().columns_types.index('is_root')
                is_root_index = model.sourceModel().index(source_index.row(), is_root_col)
                is_root = model.sourceModel().data(is_root_index, Qt.DisplayRole)

                menu = QMenu()
                if is_root:
                    unset_root = QAction(self.tr("Unset root node"), self)
                    unset_root.triggered.connect(self.unset_root_node)
                    unset_root.setData(self.community.network.root_node_index(source_index.row()))
                    if len(self.community.network.root_nodes) > 1:
                        menu.addAction(unset_root)
                else:
                    set_root = QAction(self.tr("Set as root node"), self)
                    set_root.triggered.connect(self.set_root_node)
                    set_root.setData(self.community.network.nodes[source_index.row()])
                    menu.addAction(set_root)
                # Show the context menu.
                menu.exec_(QCursor.pos())

    @pyqtSlot()
    def set_root_node(self):
        node = self.sender().data()
        self.community.network.add_root_node(node)

    @pyqtSlot()
    def unset_root_node(self):
        index = self.sender().data()
        self.community.network.remove_root_node(index)



