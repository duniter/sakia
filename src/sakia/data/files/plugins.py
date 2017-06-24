import attr
import shutil
import os
import sys
import logging
import importlib
from ..entities import Plugin


@attr.s()
class PluginsDirectory:
    """
    The repository for UserParameters
    """
    _path = attr.ib()
    plugins = attr.ib(default=[])
    with_plugin = attr.ib(default=None)
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def in_config_path(cls, config_path, profile_name="Default Profile"):
        plugins_path = os.path.join(config_path, profile_name, "plugins")
        if not os.path.exists(plugins_path):
            os.makedirs(plugins_path)
        return cls(plugins_path)

    def load_or_init(self, with_plugin=""):
        """
        Init plugins
        """
        try:
            for file in os.listdir(self._path):
                if file.endswith(".zip"):
                    sys.path.append(os.path.join(self._path, file))
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    try:
                        plugin_module = importlib.import_module(module_name)
                        self.plugins.append(Plugin(plugin_module.PLUGIN_NAME,
                                                   plugin_module.PLUGIN_DESCRIPTION,
                                                   plugin_module.PLUGIN_VERSION,
                                                   True,
                                                   plugin_module,
                                                   file))
                    except ImportError as e:
                        self.plugins.append(Plugin(module_name, "", "",
                                                   False, None, file))
                        self._logger.debug(str(e) + " with sys.path " + str(sys.path))
            if with_plugin:
                sys.path.append(with_plugin)
                module_name = os.path.splitext(os.path.basename(with_plugin))[0]
                try:
                    plugin_module = importlib.import_module(module_name)
                    self.with_plugin = Plugin(plugin_module.PLUGIN_NAME,
                                              plugin_module.PLUGIN_DESCRIPTION,
                                              plugin_module.PLUGIN_VERSION,
                                              True,
                                              plugin_module,
                                              with_plugin)
                except ImportError as e:
                    self.with_plugin = Plugin(module_name, "", "", False, None, with_plugin)
                    self._logger.debug(str(e) + " with sys.path " + str(sys.path))
        except OSError as e:
            self._logger.debug(str(e))
        return self

    def uninstall_plugin(self, plugin):
        for file in os.listdir(self._path):
            if file == plugin.filename:
                os.remove(os.path.join(self._path, file))
                self.plugins.remove(plugin)

    def install_plugin(self, filename):
        basename = os.path.basename(filename)
        if basename not in [p.filename for p in self.plugins]:
            shutil.copyfile(filename, os.path.join(self._path, basename))
            module_name = os.path.splitext(basename)[0]
            plugin = Plugin(module_name, "", "", False, None, basename)
            self.plugins.append(plugin)
            return plugin
