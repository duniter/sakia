"""
Created on 7 févr. 2014

@author: inso
"""

import logging
from logging import FileHandler
from optparse import OptionParser
from os import environ, path, makedirs


if "XDG_CONFIG_HOME" in environ:
    config_path = environ["XDG_CONFIG_HOME"]
elif "HOME" in environ:
    config_path = path.join(environ["HOME"], ".config")
elif "APPDATA" in environ:
    config_path = environ["APPDATA"]
else:
    config_path = path.dirname(__file__)

parameters = {'home': path.join(config_path, 'cutecoin'),
              'data': path.join(config_path, 'cutecoin', 'data')}


if not path.exists(parameters['home']):
    logging.info("Creating home directory")
    makedirs((parameters['home']))


def parse_arguments(argv):
    parser = OptionParser()

    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Print INFO messages to stdout")

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Print DEBUG messages to stdout")

    (options, args) = parser.parse_args(argv)

    if options.debug:
        logging.basicConfig(format='%(levelname)s:%(module)s:%(message)s',
            level=logging.DEBUG)
    elif options.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s',
            level=logging.INFO)
    else:
        logging.getLogger().propagate = False
    logging.getLogger('quamash').setLevel(logging.INFO)
    logfile = FileHandler(path.join(parameters['home'], 'cutecoin.log'))
    logging.getLogger().addHandler(logfile)
