import asyncio

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QObject
from .model import PluginsManagerModel
from .view import PluginsManagerView
import attr


@attr.s()
class PluginsManagerController(QObject):
    """
    The PluginManager view
    """

    view = attr.ib()
    model = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.view.button_box.rejected.connect(self.view.close)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a PluginManager component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app: sakia application
        :return: a new PluginManager controller
        :rtype: PluginManagerController
        """
        view = PluginsManagerView(parent.view if parent else None)
        model = PluginsManagerModel(app)
        plugin = cls(view, model)
        view.set_table_plugins_model(model.init_plugins_table())
        view.button_delete.clicked.connect(plugin.delete_plugin)
        view.button_install.clicked.connect(plugin.install_plugin)
        return plugin

    @classmethod
    def open_dialog(cls, parent, app):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.core.Community community: the community
        :return:
        """
        dialog = cls.create(parent, app)
        return dialog.exec()

    def delete_plugin(self):
        plugin_index = self.view.selected_plugin_index()
        plugin = self.model.plugin(plugin_index)
        self.model.delete_plugin(plugin)

    def install_plugin(self):

        filename = QFileDialog.getOpenFileName(self.view, self.tr("Open File"),"",
                                               self.tr("Sakia module (*.zip)"))
        if filename[0]:
            self.model.install_plugin(filename[0])

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        return future

    def exec(self):
        self.view.exec()
