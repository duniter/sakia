from ..component.controller import ComponentController
from .model import NetworkModel
from .view import NetworkView
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QCursor, QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl
from duniterpy.api import bma


class NetworkController(ComponentController):
    """
    The network panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.network.view.NetworkView: the view
        :param sakia.gui.network.model.NetworkModel model: the model
        """
        super().__init__(parent, view, model)
        table_model = self.model.init_network_table_model()
        self.view.set_network_table_model(table_model)
        self.view.manual_refresh_clicked.connect(self.refresh_nodes_manually)

    @classmethod
    def create(cls, parent, app, **kwargs):
        account = kwargs['account']
        community = kwargs['community']

        view = NetworkView(parent.view)
        model = NetworkModel(None, app, account, community)
        txhistory = cls(parent, view, model)
        model.setParent(txhistory)
        return txhistory

    def refresh_nodes_manually(self):
        self.model.refresh_nodes_once()

    def node_context_menu(self, point):
        index = self.view.table_network.indexAt(point)
        valid, node, is_root = self.model.table_model_data(index)
        if valid:
            self.view.show_menu(point, is_root)
            menu = QMenu()
            if is_root:
                unset_root = QAction(self.tr("Unset root node"), self)
                unset_root.triggered.connect(self.unset_root_node)
                unset_root.setData(node)
                if len(self.community.network.root_nodes) > 1:
                    menu.addAction(unset_root)
            else:
                set_root = QAction(self.tr("Set as root node"), self)
                set_root.triggered.connect(self.set_root_node)
                set_root.setData(node)
                menu.addAction(set_root)

            if self.app.preferences['expert_mode']:
                open_in_browser = QAction(self.tr("Open in browser"), self)
                open_in_browser.triggered.connect(self.open_node_in_browser)
                open_in_browser.setData(node)
                menu.addAction(open_in_browser)

            # Show the context menu.
            menu.exec_(QCursor.pos())

    @pyqtSlot()
    def set_root_node(self):
        node = self.sender().data()
        self.model.add_root_node(node)

    @pyqtSlot()
    def unset_root_node(self):
        node = self.sender().data()
        self.model.unset_root_node(node)

    @pyqtSlot()
    def open_node_in_browser(self):
        node = self.sender().data()
        peering = bma.network.Peering(node.endpoint.conn_handler())
        url = QUrl(peering.reverse_url("http", "/peering"))
        QDesktopServices.openUrl(url)