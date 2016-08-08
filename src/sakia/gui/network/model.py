from ..component.model import ComponentModel
from .table_model import NetworkTableModel, NetworkFilterProxyModel
from PyQt5.QtCore import QModelIndex, Qt


class NetworkModel(ComponentModel):
    """
    A network model
    """

    def __init__(self, parent, app, account, community):
        """
        Constructor of an network model

        :param sakia.gui.network.controller.NetworkController parent: the controller
        :param sakia.core.Application app: the app
        :param sakia.core.Account account: the account
        :param sakia.core.Community community: the community
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
        self.table_model = None

    def init_network_table_model(self):
        model = NetworkTableModel(self.community)
        proxy = NetworkFilterProxyModel()
        proxy.setSourceModel(model)
        self.table_model = proxy
        model.refresh_nodes()
        return self.table_model

    def refresh_nodes_once(self):
        """
        Start the refresh of the nodes
        :return:
        """
        self.community.network.refresh_once()

    def table_model_data(self, index):
        """
        Get data at given index
        :param PyQt5.QtCore.QModelIndex index:
        :return:
        """
        if index.isValid() and index.row() < self.table_model.rowCount(QModelIndex()):
            source_index = self.table_model.mapToSource(index)
            is_root_col = self.table_model.sourceModel().columns_types.index('is_root')
            is_root_index = self.table_model.sourceModel().index(source_index.row(), is_root_col)
            is_root = self.table_model.sourceModel().data(is_root_index, Qt.DisplayRole)
            node = self.community.network.nodes(source_index.row())
            return True, node, is_root
        return False, None, None

    def add_root_node(self, node):
        self.community.network.add_root_node(node)

    def unset_root_node(self, node):
        self.community.network.remove_root_node(node)

