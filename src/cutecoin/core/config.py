'''
Created on 7 févr. 2014

@author: inso
'''

import logging
from optparse import OptionParser
import os.path
import gnupg
import ucoin


home = os.path.expanduser("~")

parameters = {'home': home + '/.config/cutecoin/',
              'data': home + '/.config/cutecoin/' 'data'}


def parse_arguments(argv):
    parser = OptionParser()

    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Print INFO messages to stdout")

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Print DEBUG messages to stdout")

    parser.add_option("--home", dest="home", default=parameters['home'],
                      help="Set another home for cutecoin.")

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

    ucoin.settings['gpg'] = gnupg.GPG()
    logger = logging.getLogger("gnupg")
    logger.setLevel(logging.INFO)

    parameters['home'] = options.home

    pass
