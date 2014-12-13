'''
Created on 7 févr. 2014

@author: inso
'''

import logging
from optparse import OptionParser
from os import environ, path
import gnupg


if "XDG_CONFIG_HOME" in environ:
    config_path = environ["XDG_CONFIG_HOME"]
elif "HOME" in environ:
    config_path = environ["HOME"] + "/.config"
elif "APPDATA" in environ:
    config_path = environ["APPDATA"]
else:
    config_path = path.dirname(__file__)

parameters = {'home': config_path + '/cutecoin/',
              'data': config_path + '/cutecoin/' + 'data'}


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
        logging.basicConfig(
            format='%(levelname)s:%(module)s:%(message)s',
            level=logging.DEBUG)
    elif options.verbose:
        logging.basicConfig(
            format='%(levelname)s:%(message)s',
            level=logging.INFO)
    else:
        logging.getLogger().propagate = False

    pass
