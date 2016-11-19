from PyQt5.QtCore import Qt
from sakia.gui.component.model import ComponentModel
from .table_model import IdentitiesFilterProxyModel, IdentitiesTableModel


class IdentitiesModel(ComponentModel):
    """
    The model of the identities component
    """

    def __init__(self, parent, app, connection, blockchain_service, identities_service):
        """
        Constructor of a model of Identities component

        :param sakia.gui.identities.controller.IdentitiesController parent: the controller
        :param sakia.app.Application app: the app
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service

        self.table_model = None

    def init_table_model(self):
        """
        Instanciate the table model of the view
        """
        identities_model = IdentitiesTableModel(self, self.blockchain_service, self.identities_service)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_model = proxy
        return self.table_model

    def table_data(self, index):
        """
        Get table data at given point
        :param PyQt5.QtCore.QModelIndex index:
        :return: a tuple containing information of the table
        """
        if index.isValid() and index.row() < self.table_model.rowCount():
            source_index = self.table_model.mapToSource(index)
            identity_col = self.table_model.sourceModel().columns_ids.index('identity')
            identity_index = self.table_model.sourceModel().index(source_index.row(),
                                                                  identity_col)
            identity = self.table_model.sourceModel().data(identity_index, Qt.DisplayRole)
            return True, identity
        return False, None

    async def lookup_identities(self, text):
        """
        Lookup for identities
        :param str text: text contained in the identities to lookup
        """
        return await self.identities_service.lookup(text)

    def refresh_identities(self, identities):
        """
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        """
        self.table_model.sourceModel().refresh_identities(identities)
