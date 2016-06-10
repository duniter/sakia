import aiohttp
import unittest
from unittest.mock import PropertyMock
from asynctest import Mock, patch
from duniterpy.documents.block import BlockUID
from PyQt5.QtCore import QLocale
from sakia.core.net import Network
from sakia.tests import QuamashTest


class TestCommunity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()
