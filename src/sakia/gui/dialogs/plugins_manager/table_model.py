from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel,\
    QModelIndex, QT_TRANSLATE_NOOP
from sakia.data.entities import Plugin


class PluginsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        """
        super().__init__(parent)
        self.app = None

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 1

    def setSourceModel(self, source_model):
        self.app = source_model.app
        super().setSourceModel(source_model)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)
        return left_data < right_data

    def plugin_name(self, index):
        """
        Gets available table data at given index
        :param index:
        :return: tuple containing (Identity, Transfer)
        """
        if index.isValid() and index.row() < self.rowCount(QModelIndex()):
            source_index = self.mapToSource(index)
            plugin_name_col = PluginsTableModel.columns_types.index('name')
            plugin_name = self.sourceModel().plugins_data[source_index.row()][plugin_name_col]
            return plugin_name
        return None
    
    def data(self, index, role):
        source_index = self.mapToSource(index)
        model = self.sourceModel()
        source_data = model.data(source_index, role)
        return source_data


class PluginsTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display plugins in a table view
    """

    columns_types = (
        'name',
        'description',
        'version',
        'imported'
    )

    columns_headers = (
        QT_TRANSLATE_NOOP("PluginsTableModel", 'Name'),
        QT_TRANSLATE_NOOP("PluginsTableModel", 'Description'),
        QT_TRANSLATE_NOOP("PluginsTableModel", 'Version'),
        QT_TRANSLATE_NOOP("PluginsTableModel", 'Imported'),
    )

    def __init__(self, parent, app):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        :param sakia.app.Application app: the main application
        """
        super().__init__(parent)
        self.app = app
        self.plugins_data = []

    def add_plugin(self, plugin):
        self.beginInsertRows(QModelIndex(), len(self.plugins_data), len(self.plugins_data))
        self.plugins_data.append(self.data_plugin(plugin))
        self.endInsertRows()

    def remove_plugin(self, plugin):
        for i, data in enumerate(self.plugins_data):
            if data[PluginsTableModel.columns_types.index('name')] == plugin.name:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.plugins_data.pop(i)
                self.endRemoveRows()
                return

    def data_plugin(self, plugin):
        """
        Converts a plugin to table data
        :param sakia.data.entities.Plugin plugin: the plugin
        :return: data as tuple
        """
        return plugin.name, plugin.description, plugin.version, plugin.imported

    def init_plugins(self):
        self.beginResetModel()
        self.plugins_data = []
        for plugin in self.app.plugins_dir.plugins:
            self.plugins_data.append(self.data_plugin(plugin))
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.plugins_data)

    def columnCount(self, parent):
        return len(PluginsTableModel.columns_types)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return PluginsTableModel.columns_headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        if role in (Qt.DisplayRole, Qt.ForegroundRole, Qt.ToolTipRole):
            return self.plugins_data[row][col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

