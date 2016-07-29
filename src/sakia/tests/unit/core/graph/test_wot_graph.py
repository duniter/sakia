import sys
import unittest
import logging
from asynctest.mock import Mock, CoroutineMock, patch
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.graph import WoTGraph
from sakia.core.graph.constants import EdgeStatus, NodeStatus


class TestWotGraph(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        ## Graph to test :
        ##
        ## A - B - C
        ##
        ## Path : Between A and C

        self.account_identity = Mock(specs='core.registry.Identity')
        self.account_identity.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.account_identity.uid = "A"
        self.account_identity.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.idB = Mock(specs='core.registry.Identity')
        self.idB.pubkey = "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        self.idB.uid = "B"
        self.idB.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.idC = Mock(specs='core.registry.Identity')
        self.idC.pubkey = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
        self.idC.uid = "C"
        self.idC.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=False)

        self.account_identity.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49800,
                                                                   'identity': self.idB,
                                                                   'block_number': 996
                                                               }
                                                           ])
        self.account_identity.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[])

        self.idC.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certifierd_by',
                                                           return_value=[])

        self.idC.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idB,
                                                                   'block_number': 990
                                                               }
                                                           ])

        self.idB.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idC,
                                                                   'block_number': 996
                                                               }
                                                           ])

        self.idB.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49800,
                                                                   'identity': self.account_identity,
                                                                   'block_number': 996
                                                               }
                                                           ])

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_explore_to_find_member(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        wot_graph = WoTGraph(app, community)

        async def exec_test():
            result = await wot_graph.explore_to_find_member(self.account_identity, self.idC)
            self.assertTrue(result)
            self.assertEqual(len(wot_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(wot_graph.nx_graph.edges()), 2)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('time.time', Mock(return_value=50000))
    def test_explore_to_find_unknown(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        wot_graph = WoTGraph(app, community)

        identity_unknown = Mock(specs='core.registry.Identity')
        identity_unknown.pubkey = "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        identity_unknown.uid = "unkwn"

        async def exec_test():
            result = await wot_graph.explore_to_find_member(self.account_identity, identity_unknown)
            self.assertFalse(result)
            self.assertEqual(len(wot_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(wot_graph.nx_graph.edges()), 2)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_shortest_path(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        wot_graph = WoTGraph(app, community)

        async def exec_test():
            result = await wot_graph.explore_to_find_member(self.account_identity, self.idC)
            self.assertTrue(result)
            self.assertEqual(len(wot_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(wot_graph.nx_graph.edges()), 2)
            path = await wot_graph.get_shortest_path_to_identity(self.account_identity, self.idC)
            self.assertEqual(path[0], self.account_identity.pubkey,)
            self.assertEqual(path[1], self.idB.pubkey)
            self.assertEqual(path[2], self.idC.pubkey)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_initialize(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        wot_graph = WoTGraph(app, community)

        async def exec_test():
            await wot_graph.initialize(self.account_identity, self.account_identity)
            self.assertEqual(len(wot_graph.nx_graph.nodes()), 2)
            self.assertEqual(len(wot_graph.nx_graph.edges()), 1)

        self.lp.run_until_complete(exec_test())
