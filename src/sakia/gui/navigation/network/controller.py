from .model import NetworkModel
from .view import NetworkView
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QCursor, QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl, QObject
from duniterpy.api import bma
from duniterpy.documents import BMAEndpoint


class NetworkController(QObject):
    """
    The network panel
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.network.view.NetworkView: the view
        :param sakia.gui.network.model.NetworkModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        table_model = self.model.init_network_table_model()
        self.view.set_network_table_model(table_model)
        self.view.manual_refresh_clicked.connect(self.refresh_nodes_manually)
        self.view.table_network.customContextMenuRequested.connect(self.node_context_menu)

    @classmethod
    def create(cls, parent, app, network_service):
        """

        :param PyQt5.QObject parent:
        :param sakia.app.Application app:
        :param sakia.services.NetworkService network_service:
        :return:
        """
        view = NetworkView(parent.view,)
        model = NetworkModel(None, app, network_service)
        txhistory = cls(parent, view, model)
        model.setParent(txhistory)
        return txhistory
    
    def refresh_nodes_manually(self):
        self.model.refresh_nodes_once()

    def node_context_menu(self, point):
        index = self.view.table_network.indexAt(point)
        valid, node = self.model.table_model_data(index)
        if self.model.app.parameters.expert_mode:
            menu = QMenu()
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
        bma_endpoints = [e for e in node.endpoints if isinstance(e, BMAEndpoint)]
        if bma_endpoints:
            conn_handler = next(bma_endpoints[0].conn_handler())
            peering_url = bma.API(conn_handler, bma.network.URL_PATH).reverse_url(conn_handler.http_scheme, '/peering')
            url = QUrl(peering_url)
            QDesktopServices.openUrl(url)
