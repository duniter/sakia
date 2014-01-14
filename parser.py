#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#

import argparse, logging, sys
from collections import OrderedDict

class Parser(argparse.ArgumentParser):
    """Wrapper class added logging support"""

    def __init__(self, description='', verbose='quiet', formatter_class=argparse.ArgumentDefaultsHelpFormatter):
        """
        We add all the common options to manage verbosity.
        """

        argparse.ArgumentParser.__init__(self, description=description, formatter_class=formatter_class)

        self.levels = OrderedDict([('debug', logging.DEBUG),
                                   ('info', logging.INFO),
                                   ('warning', logging.WARNING),
                                   ('error', logging.ERROR),
                                   ('quiet', logging.CRITICAL),
                                   ])

        self.add_argument('--verbose', '-v', choices=[x for x in self.levels.keys()], default=verbose, help='set a verbosity level')
        self.add_argument('--levels', '-l', action='store_true', default=False, help='list all the verbosity levels')
        self.add_argument('--output', '-o', help='all the logging messages are redirected to the specified filename.')
        self.add_argument('--debug', '-d', action='store_const', const='debug', dest='verbose', help='Diplay all the messages.')
        self.add_argument('--info', '-i', action='store_const', const='info', dest='verbose', help='Diplay the info messages.')
        self.add_argument('--warning', '-w', action='store_const', const='warning', dest='verbose', help='Only diplay the warning and error messages.')
        self.add_argument('--error', '-e', action='store_const', const='error', dest='verbose', help='Only diplay the error messages')
        self.add_argument('--quiet', '-q', action='store_const', const='quiet', dest='verbose', help='Quiet level of verbosity only displaying the critical error messages.')

    def __call__(self):
        args = self.parse_args()

        if args.levels:
            print("Here's the verbose levels available:")
            for keys in self.levels.keys():
                print("\t", keys)
            sys.exit()

        if (args.output):
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                filename=args.output, filemode='a'
                )
        else:
            logging.basicConfig(
                level=self.levels.get(args.verbose, logging.NOTSET),
                format='%(name)-12s: %(levelname)-8s %(message)s'
            )

        return args
