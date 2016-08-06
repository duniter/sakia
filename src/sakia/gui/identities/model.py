from PyQt5.QtCore import Qt
from ..component.model import ComponentModel
from .table_model import IdentitiesFilterProxyModel, IdentitiesTableModel


class IdentitiesModel(ComponentModel):
    """
    The model of the identities component
    """

    def __init__(self, parent, app, account, community):
        """
        Constructor of a model of Identities component

        :param sakia.gui.identities.controller.IdentitiesController parent: the controller
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community

        self.table_model = None

    def init_table_model(self):
        """
        Instanciate the table model of the view
        """
        identities_model = IdentitiesTableModel(self, self.community)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_model = proxy
        return self.table_model

    async def table_data(self, index):
        """
        Get table data at given point
        :param PyQt5.QtCore.QModelIndex index:
        :return: a tuple containing information of the table
        """
        if index.isValid() and index.row() < self.table_model.rowCount():
            source_index = self.table_model.mapToSource(index)
            pubkey_col = self.table_model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = self.table_model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = self.table_model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = await self.app.identities_registry.future_find(pubkey, self.community)
            return True, identity
        return False, None

    async def refresh_identities(self, identities):
        """
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        """
        await self.table_model.sourceModel().refresh_identities(identities)
