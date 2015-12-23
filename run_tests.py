import sys
import os
import signal
import unittest
import subprocess
import time
import shlex
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-u", "--unit",
                  action="store_true", dest="unit", default=False,
                  help="Run unit tests")

parser.add_option("-f", "--functional",
                  action="store_true", dest="functional", default=False,
                  help="Run functional tests")

parser.add_option("-a", "--all",
                  action="store_true", dest="all", default=False,
                  help="Run all tests")
options, args = parser.parse_args(sys.argv)

if options.unit:
    runner = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='sakia.tests.unit',
                                                                               pattern='test_*'))
elif options.functional:
    runner = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='sakia.tests.functional',
                                                                               pattern='test_*'))
elif options.all:
    runner = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='sakia.tests',
                                                                               pattern='test_*'))
else:
    parser.print_help()
    sys.exit(1)

sys.exit(not runner.wasSuccessful())