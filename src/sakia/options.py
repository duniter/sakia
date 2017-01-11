"""
Created on 7 févr. 2014

@author: inso
"""

import attr
import logging
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler
from optparse import OptionParser
from os import environ, path, makedirs


def config_path_factory():
    if "XDG_CONFIG_HOME" in environ:
        env_path = environ["XDG_CONFIG_HOME"]
    elif "HOME" in environ:
        env_path = path.join(environ["HOME"], ".config")
    elif "APPDATA" in environ:
        env_path = environ["APPDATA"]
    else:
        env_path = path.dirname(__file__)
    return path.join(env_path, 'sakia')


@attr.s()
class SakiaOptions:
    config_path = attr.ib(default=attr.Factory(config_path_factory))
    database = attr.ib(default="sakia")
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

        parser.add_option("--database",  dest="database", default="sakia",
                          help="Select another database filename")

        (options, args) = parser.parse_args(argv)

        if options.database:
            self.database = options.database

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
