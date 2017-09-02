import attr
import logging
from sakia.constants import ROOT_SERVERS
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler
from optparse import OptionParser
from os import environ, path, makedirs
import sys


def config_path_factory():
    if sys.platform.startswith("darwin") and "XDG_CONFIG_HOME" in environ:
        env_path = environ["XDG_CONFIG_HOME"]
    elif sys.platform.startswith("linux") and "HOME" in environ:
        env_path = path.join(environ["HOME"], ".config")
    elif sys.platform.startswith("win32") and"APPDATA" in environ:
        env_path = environ["APPDATA"]
    else:
        env_path = path.dirname(__file__)
    return path.join(env_path, 'sakia')


@attr.s()
class SakiaOptions:
    config_path = attr.ib(default=attr.Factory(config_path_factory))
    currency = attr.ib(default="gtest")
    profile = attr.ib(default="Default Profile")
    with_plugin = attr.ib(default="")
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def from_arguments(cls, argv):
        options = cls()

        if not path.exists(options.config_path):
            makedirs(options.config_path)

        options._parse_arguments(argv)

        return options

    def _parse_arguments(self, argv):
        parser = OptionParser()
        parser.add_option("-v", "--verbose",
                          action="store_true", dest="verbose", default=False,
                          help="Print INFO messages to stdout")

        parser.add_option("-d", "--debug",
                          action="store_true", dest="debug", default=False,
                          help="Print DEBUG messages to stdout")

        parser.add_option("--currency",  dest="currency", default="g1",
                          help="Select a currency between {0}".format(",".join(ROOT_SERVERS.keys())))

        parser.add_option("--profile",  dest="profile", default="Default Profile",
                          help="Select profile to use")

        parser.add_option("--withplugin",  dest="with_plugin", default="",
                          help="Load a plugin (for development purpose)")

        (options, args) = parser.parse_args(argv)

        if options.currency not in ROOT_SERVERS.keys():
            raise RuntimeError("{0} is not a valid currency".format(options.currency))
        else:
            self.currency = options.currency

        if options.profile:
            self.profile = options.profile

        if options.with_plugin:
            if path.isfile(options.with_plugin) and options.with_plugin.endswith(".zip"):
                self.with_plugin = options.with_plugin
            else:
                raise RuntimeError("{:} is not a valid path to a zip file".format(options.with_plugin))

        if options.debug:
            self._logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s:%(module)s:%(funcName)s:%(message)s')
        elif options.verbose:
            self._logger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s:%(message)s')

        if options.debug or options.verbose:
            logging.getLogger('quamash').setLevel(logging.INFO)
            file_handler = RotatingFileHandler(path.join(self.config_path, 'sakia.log'), 'a', 1000000, 10)
            file_handler.setFormatter(formatter)
            stream_handler = StreamHandler()
            stream_handler.setFormatter(formatter)
            self._logger.handlers = [file_handler, stream_handler]
            self._logger.propagate = False
