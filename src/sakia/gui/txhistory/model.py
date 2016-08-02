from sakia.gui.component.model import ComponentModel
from .table_model import HistoryTableModel, TxFilterProxyModel
from PyQt5.QtCore import Qt


class TxHistoryModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community

    def history_table_model(self, ts_from, ts_to):
        """
        Generates a history table model
        :param int ts_from: date from where to filter tx
        :param int ts_to: date to where to filter tx
        :return:
        """
        model = HistoryTableModel(self.app, self.account, self.community)
        proxy = TxFilterProxyModel(ts_from, ts_to)
        proxy.setSourceModel(model)
        proxy.setDynamicSortFilter(True)
        proxy.setSortRole(Qt.DisplayRole)
        return proxy