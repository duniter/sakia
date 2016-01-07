import sys
import unittest
import logging
import time
import asyncio
import json
from aiohttp import web
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


class TestIdentity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50009)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.12.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

    def tearDown(self):
        self.tearDownQuamash()

    def test_identity_certifiers_of(self):
        mock = nice_blockchain.get_mock(self.lp)

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", 1441130831,
                            LocalState.COMPLETED, BlockchainState.VALIDATED)

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.endpoint.port = port
            certifiers = await identity.certifiers_of(self.identities_registry, self.community)

            self.assertEqual(len(certifiers), 1)
            self.assertEqual(certifiers[0]['identity'].uid, "doe")
            # Force one more loop turn
            await asyncio.sleep(0)

        self.lp.run_until_complete(exec_test())

    def test_identity_membership(self):
        mock = nice_blockchain.get_mock(self.lp)
        time.sleep(2)
        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", 1441130831,
                            LocalState.COMPLETED, BlockchainState.VALIDATED)

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.endpoint.port = port
            ms = await identity.membership(self.community)
            self.assertEqual(ms["blockNumber"], 0)
            self.assertEqual(ms["blockHash"], "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709")
            self.assertEqual(ms["membership"], "IN")
            self.assertEqual(ms["currency"], "test_currency")

        self.lp.run_until_complete(exec_test())

    def test_identity_corrupted_membership(self):
        mock = corrupted.get_mock(self.lp)
        time.sleep(2)
        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", 1441130831,
                            LocalState.COMPLETED, BlockchainState.VALIDATED)

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.endpoint.port = port
            with self.assertRaises(MembershipNotFoundError):
                await identity.membership(self.community)

        self.lp.run_until_complete(exec_test())

