from .table_model import NetworkTableModel, NetworkFilterProxyModel
from PyQt5.QtCore import QModelIndex, Qt, QObject


class NetworkModel(QObject):
    """
    A network model
    """

    def __init__(self, parent, app, network_service):
        """
        Constructor of an network model

        :param sakia.gui.network.controller.NetworkController parent: the controller
        :param sakia.app.Application app: the app
        :param sakia.services.NetworkService network_service: the service handling network state
        """
        super().__init__(parent)
        self.app = app
        self.network_service = network_service
        self.table_model = None

    def init_network_table_model(self):
        model = NetworkTableModel(self.network_service)
        proxy = NetworkFilterProxyModel(self.app)
        proxy.setSourceModel(model)
        self.table_model = proxy
        model.init_nodes()
        return self.table_model

    def refresh_nodes_once(self):
        """
        Start the refresh of the nodes
        :return:
        """
        self.network_service.refresh_once()

    def table_model_data(self, index):
        """
        Get data at given index
        :param PyQt5.QtCore.QModelIndex index:
        :return:
        """
        if index.isValid() and index.row() < self.table_model.rowCount(QModelIndex()):
            source_index = self.table_model.mapToSource(index)
            node = self.network_service.nodes()[source_index.row()]
            return True, node
        return False, None
