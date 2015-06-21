import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

runner = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='cutecoin.tests', pattern='test_*'))

sys.exit(not runner.wasSuccessful())