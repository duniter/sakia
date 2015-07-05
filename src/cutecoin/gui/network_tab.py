"""
Created on 20 févr. 2015

@author: inso
"""

import logging
import asyncio

from PyQt5.QtGui import QCursor, QDesktopServices
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QModelIndex, pyqtSlot, QUrl
from ..models.network import NetworkTableModel, NetworkFilterProxyModel
from ..core.net.api import bma as qtbma
from ..gen_resources.network_tab_uic import Ui_NetworkTabWidget


class NetworkTabWidget(QWidget, Ui_NetworkTabWidget):
    """
    classdocs
    """

    def __init__(self, app, community):
        """
        Constructore of a network tab.

        :param cutecoin.core.Application app: The application
        :param cutecoin.core.Community community: The community
        :return: A new network tab.
        :rtype: NetworkTabWidget
        """
        super().__init__()
        self.app = app
        self.community = community

        self.setupUi(self)
        model = NetworkTableModel(community)
        proxy = NetworkFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.table_network.setModel(proxy)
        self.table_network.sortByColumn(0, Qt.DescendingOrder)
        self.table_network.resizeColumnsToContents()
        community.network.nodes_changed.connect(self.refresh_nodes)

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

            if self.app.preferences['expert_mode']:
                open_in_browser = QAction(self.tr("Open in browser"), self)
                open_in_browser.triggered.connect(self.open_node_in_browser)
                open_in_browser.setData(self.community.network.nodes[source_index.row()])
                menu.addAction(open_in_browser)

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

    @pyqtSlot()
    def open_node_in_browser(self):
        node = self.sender().data()
        peering = qtbma.network.Peering(node.endpoint)
        url = QUrl(peering.reverse_url("/peering"))
        QDesktopServices.openUrl(url)

    def manual_nodes_refresh(self):
        self.community.network.refresh_once()


