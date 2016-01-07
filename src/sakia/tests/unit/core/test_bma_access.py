import sys
import unittest
import asyncio
import quamash
import logging
import time
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import Identity, IdentitiesRegistry, LocalState, BlockchainState

from sakia.tests.mocks.bma import nice_blockchain, corrupted
from sakia.tests import QuamashTest
from sakia.core import Application, Community
from sakia.core.net import Network, Node
from ucoinpy.documents.peer import BMAEndpoint
from sakia.core.net.api.bma.access import BmaAccess
from sakia.tools.exceptions import MembershipNotFoundError
from ucoinpy.api.bma import API


class TestBmaAccess(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50004)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.12.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

    def tearDown(self):
        self.tearDownQuamash()

    def test_compare_json_with_nonetype(self):
        res = self.bma_access._compare_json({}, corrupted.bma_null_data)
        self.assertFalse(res)

    def test_filter_nodes(self):
        pass#TODO
