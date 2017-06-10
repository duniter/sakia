from PyQt5.QtCore import QObject


class MainWindowModel(QObject):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def load_plugins(self, main_window):
        for plugin in self.app.plugins_dir.plugins:
            if plugin.imported:
                plugin.module.plugin_exec(self.app, main_window)
        if self.app.plugins_dir.with_plugin and self.app.plugins_dir.with_plugin.module:
            self.app.plugins_dir.with_plugin.module.plugin_exec(self.app, main_window)
