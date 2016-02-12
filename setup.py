import sys, os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

if "test" in sys.argv:
    print(sys.path)
    if "XDG_CONFIG_HOME" in os.environ:
        os.environ["XDG_CONFIG_HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp'))
    elif "HOME" in os.environ:
        os.environ["HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp'))
    elif "APPDATA" in os.environ:
        os.environ["APPDATA"] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp'))
    runner = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(start_dir='sakia.tests',
                                                                               pattern='test_*'))

    sys.exit(not runner.wasSuccessful())