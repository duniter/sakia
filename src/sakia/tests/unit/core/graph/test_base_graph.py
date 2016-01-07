import sys
import unittest
import logging
from asynctest.mock import Mock, CoroutineMock, patch
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.graph import BaseGraph
from sakia.core.graph.constants import EdgeStatus, NodeStatus


class TestBaseGraph(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.account_identity = Mock(specs='core.registry.Identity')
        self.account_identity.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.account_identity.uid = "account_identity"
        self.account_identity.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.first_identity = Mock(specs='core.registry.Identity')
        self.first_identity.pubkey = "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        self.first_identity.uid = "first_identity"
        self.first_identity.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.second_identity = Mock(specs='core.registry.Identity')
        self.second_identity.pubkey = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
        self.second_identity.uid = "second_uid"
        self.second_identity.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=False)

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('time.time', Mock(return_value=50000))
    def test_arc_status(self, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        app = Mock()

        base_graph = BaseGraph(app, community)

        async def exec_test():
            self.assertEquals((await base_graph.arc_status(48000)), EdgeStatus.WEAK)
            self.assertEquals((await base_graph.arc_status(49500)), EdgeStatus.STRONG)
            self.assertEquals((await base_graph.arc_status(49200)), EdgeStatus.WEAK)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    def test_node_status_member(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})

        base_graph = BaseGraph(app, community)
        certifier = Mock(specs='core.registry.Identity')
        certifier.pubkey = "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        certifier.uid = "first_identity"
        certifier.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=False)

        account_identity = Mock(specs='core.registry.Identity')
        account_identity.pubkey = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
        account_identity.uid = "second_uid"
        account_identity.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        async def exec_test():
            self.assertEquals((await base_graph.node_status(certifier, account_identity)), NodeStatus.OUT)
            self.assertEquals((await base_graph.node_status(account_identity, account_identity)), NodeStatus.HIGHLIGHTED)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    def test_confirmation_text_expert_enabled(self, app, community):
        community.network.confirmations = Mock(return_value=2)
        app.preferences = {'expert_mode': True}

        base_graph = BaseGraph(app, community)

        async def exec_test():
            self.assertEquals((await base_graph.confirmation_text(200)), "2/6")

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    def test_confirmation_text_expert_disabled(self, app, community):
        community.network.confirmations = Mock(return_value=2)
        app.preferences = {'expert_mode': False}

        base_graph = BaseGraph(app, community)

        async def exec_test():
            self.assertEquals((await base_graph.confirmation_text(200)), "33 %")

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('time.time', Mock(return_value=950000))
    def test_add_identitiers(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        base_graph = BaseGraph(app, community)

        certifications = [
            {
                'identity': self.first_identity,
                'cert_time': 949100,
                'block_number': 900
            },
            {
                'identity': self.second_identity,
                'cert_time': 949800,
                'block_number': 996
            }
        ]
        async def exec_test():
            await base_graph.add_certifier_list(certifications, self.account_identity, self.account_identity)
            self.assertEqual(len(base_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(base_graph.nx_graph.edges()), 2)
            nodes = base_graph.nx_graph.nodes(data=True)
            edges = base_graph.nx_graph.edges(data=True)

            first_node = [n for n in nodes if n[0] == self.first_identity.pubkey][0]
            self.assertEqual(first_node[1]['status'], NodeStatus.NEUTRAL)
            self.assertEqual(first_node[1]['text'], certifications[0]['identity'].uid)
            self.assertEqual(first_node[1]['tooltip'], certifications[0]['identity'].pubkey)

            second_node = [n for n in nodes if n[0] == self.second_identity.pubkey][0]
            self.assertEqual(second_node[1]['status'], NodeStatus.OUT)
            self.assertEqual(second_node[1]['text'], certifications[1]['identity'].uid)
            self.assertEqual(second_node[1]['tooltip'], certifications[1]['identity'].pubkey)

            arc_from_first = [e for e in edges if e[0] == self.first_identity.pubkey][0]
            self.assertEqual(arc_from_first[1], self.account_identity.pubkey)
            self.assertEqual(arc_from_first[2]['status'], EdgeStatus.WEAK)
            self.assertEqual(arc_from_first[2]['cert_time'], certifications[0]['cert_time'])

            arc_from_second = [e for e in edges if e[0] == self.second_identity.pubkey][0]
            self.assertEqual(arc_from_second[1], self.account_identity.pubkey)
            self.assertEqual(arc_from_second[2]['status'], EdgeStatus.STRONG)
            self.assertEqual(arc_from_second[2]['cert_time'], certifications[1]['cert_time'])

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('time.time', Mock(return_value=50000))
    def test_add_certified(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        base_graph = BaseGraph(app, community)

        certifications = [
            {
                'identity': self.first_identity,
                'cert_time': 49100,
                'block_number': 900
            },
            {
                'identity': self.second_identity,
                'cert_time': 49800,
                'block_number': 996
            }
        ]
        async def exec_test():
            await base_graph.add_certified_list(certifications, self.account_identity, self.account_identity)
            self.assertEqual(len(base_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(base_graph.nx_graph.edges()), 2)
            nodes = base_graph.nx_graph.nodes(data=True)
            first_node = [n for n in nodes if n[0] == self.first_identity.pubkey][0]
            self.assertEqual(first_node[1]['status'], NodeStatus.NEUTRAL)
            self.assertEqual(first_node[1]['text'], certifications[0]['identity'].uid)
            self.assertEqual(first_node[1]['tooltip'], certifications[0]['identity'].pubkey)

            second_node = [n for n in nodes if n[0] == self.second_identity.pubkey][0]
            self.assertEqual(second_node[1]['status'], NodeStatus.OUT)
            self.assertEqual(second_node[1]['text'], certifications[1]['identity'].uid)
            self.assertEqual(second_node[1]['tooltip'], certifications[1]['identity'].pubkey)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('time.time', Mock(return_value=50000))
    def test_add_identity(self, app, community):
        app.preferences = {'expert_mode': True}

        base_graph = BaseGraph(app, community)

        base_graph.add_identity(self.account_identity, NodeStatus.HIGHLIGHTED)
        self.assertEqual(len(base_graph.nx_graph.nodes()), 1)
        self.assertEqual(len(base_graph.nx_graph.edges()), 0)
        nodes = base_graph.nx_graph.nodes(data=True)
        account_node = [n for n in nodes if n[0] == self.account_identity.pubkey][0]
        self.assertEqual(account_node[1]['status'], NodeStatus.HIGHLIGHTED)
        self.assertEqual(account_node[1]['text'], self.account_identity.uid)
        self.assertEqual(account_node[1]['tooltip'], self.account_identity.pubkey)
