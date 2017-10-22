from PyQt5.QtWidgets import QWidget, QHeaderView
from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from .network_uic import Ui_NetworkWidget
from .delegate import NetworkDelegate
import asyncio


class NetworkView(QWidget, Ui_NetworkWidget):
    """
    The view of Network component
    """
    manual_refresh_clicked = pyqtSignal()

    def __init__(self, parent):
        """

        :param sakia.gui.network.controller parent:
        """
        super().__init__(parent)
        self.setupUi(self)

    def set_network_table_model(self, model):
        """
        Set the table view model
        :param PyQt5.QtCore.QAbstractTableModel model: the model of the table view
        """
        self.table_network.setModel(model)
        self.table_network.sortByColumn(3, Qt.DescendingOrder)
        self.table_network.setItemDelegate(NetworkDelegate())
        self.table_network.resizeColumnsToContents()
        self.table_network.resizeRowsToContents()
        self.table_network.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def manual_nodes_refresh(self):
        self.button_manual_refresh.setEnabled(False)
        asyncio.get_event_loop().call_later(15, lambda: self.button_manual_refresh.setEnabled(True))
        self.manual_refresh_clicked.emit()

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super().changeEvent(event)
