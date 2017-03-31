from PyQt5.QtCore import QObject, Qt
from .table_model import PluginsTableModel, PluginsFilterProxyModel
import attr


@attr.s()
class PluginsManagerModel(QObject):
    """
    The model of Plugin component

    :param sakia.app.Application app: The application
    """

    app = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()

    def init_plugins_table(self):
        """
        Generates a plugins table model
        :return:
        """
        self._model = PluginsTableModel(self, self.app)
        self._proxy = PluginsFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setDynamicSortFilter(True)
        self._proxy.setSortRole(Qt.DisplayRole)
        self._model.init_plugins()
        return self._proxy

    def delete_plugin(self, plugin):
        self.app.plugins_dir.uninstall_plugin(plugin)
        self._model.remove_plugin(plugin)

    def plugin(self, index):
        plugin_name = self._proxy.plugin_name(index)
        if plugin_name:
            try:
                return next(p for p in self.app.plugins_dir.plugins if p.name == plugin_name)
            except StopIteration:
                pass
        return None

    def install_plugin(self, filename):
        try:
            plugin = self.app.plugins_dir.install_plugin(filename)
            self._model.add_plugin(plugin)
        except OSError as e:
            self.view.show_error(str(e))
