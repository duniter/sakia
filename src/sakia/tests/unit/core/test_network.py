import sys
import unittest
from unittest.mock import PropertyMock
from asynctest import Mock, patch
from ucoinpy.documents.block import BlockId
from PyQt5.QtCore import QLocale
from sakia.core.net import Network
from sakia.tests import QuamashTest


class TestCommunity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_confirmations(self):
        network = Network("test_currency", [])
        Network.current_blockid = PropertyMock(return_value=BlockId(1000, "fbf9271d0df23ee03044795aebca8be06dd7f998".upper()))

        self.assertEqual(network.confirmations(996), 5)
        self.assertEqual(network.confirmations(900), 101)
        with self.assertRaises(ValueError):
            network.confirmations(1002)
