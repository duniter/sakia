from PyQt5.QtWidgets import QDialog, QAbstractItemView, QHeaderView, QMessageBox
from PyQt5.QtCore import QModelIndex
from .plugins_manager_uic import Ui_PluginDialog


class PluginsManagerView(QDialog, Ui_PluginDialog):
    """
    The view of the plugins manager component
    """

    def __init__(self, parent):
        """

        :param parent:
        """
        super().__init__(parent)
        self.setupUi(self)

    def set_table_plugins_model(self, model):
        """
        Define the table history model
        :param QAbstractItemModel model:
        :return:
        """
        self.table_plugins.setModel(model)
        self.table_plugins.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_plugins.setSortingEnabled(True)
        self.table_plugins.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_plugins.resizeRowsToContents()
        self.table_plugins.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def selected_plugin_index(self):
        indexes = self.table_plugins.selectedIndexes()
        if indexes:
            return indexes[0]
        return QModelIndex()

    def show_error(self, error_txt):
        QMessageBox.critical(self, self.tr("Plugin import"),
                             self.tr("CCould not import plugin : {0}".format(error_txt)))
