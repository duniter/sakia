import unittest

# run all tests
unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='cutecoin.tests', pattern='test_*'))
