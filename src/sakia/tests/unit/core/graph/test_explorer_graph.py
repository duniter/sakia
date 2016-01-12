import sys
import unittest
import asyncio
from asynctest.mock import Mock, CoroutineMock, patch
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.graph import ExplorerGraph


class TestExplorerGraph(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        ## Graph to test :
        ##           - E
        ## A - B - C - D
        ##
        ## Path : Between A and C

        self.idA = Mock(specs='core.registry.Identity')
        self.idA.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.idA.uid = "A"
        self.idA.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.idB = Mock(specs='core.registry.Identity')
        self.idB.pubkey = "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        self.idB.uid = "B"
        self.idB.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.idC = Mock(specs='core.registry.Identity')
        self.idC.pubkey = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
        self.idC.uid = "C"
        self.idC.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=False)

        self.idD = Mock(specs='core.registry.Identity')
        self.idD.pubkey = "6R11KGpG6w5Z6JfiwaPf3k4BCMY4dwhjCdmjGpvn7Gz5"
        self.idD.uid = "D"
        self.idD.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=True)

        self.idE = Mock(specs='core.registry.Identity')
        self.idE.pubkey = "CZVDEsM6pPNxhAvXApGM8MJ6ExBZVpc8PNVyDZ7hKxLu"
        self.idE.uid = "E"
        self.idE.is_member = CoroutineMock(spec='core.registry.Identity.is_member', return_value=False)

        self.idA.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49800,
                                                                   'identity': self.idB,
                                                                   'block_number': 996
                                                               }
                                                           ])
        self.idA.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[])

        self.idB.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idC,
                                                                   'block_number': 990
                                                               }
                                                           ])

        self.idB.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49800,
                                                                   'identity': self.idA,
                                                                   'block_number': 996
                                                               }
                                                           ])

        self.idC.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idD,
                                                                   'block_number': 990
                                                               },
                                                               {
                                                                   'cert_time': 49110,
                                                                   'identity': self.idE,
                                                                   'block_number': 990
                                                               }
                                                           ])

        self.idC.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idB,
                                                                   'block_number': 990
                                                               }
                                                           ])

        self.idD.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                           ])
        self.idD.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idC,
                                                                   'block_number': 990
                                                               }])

        self.idE.unique_valid_certified_by = CoroutineMock(spec='core.registry.Identity.certified_by',
                                                           return_value=[
                                                           ])
        self.idE.unique_valid_certifiers_of = CoroutineMock(spec='core.registry.Identity.certifiers_of',
                                                           return_value=[
                                                               {
                                                                   'cert_time': 49100,
                                                                   'identity': self.idC,
                                                                   'block_number': 990
                                                               }])

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_explore_full_from_center(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        explorer_graph = ExplorerGraph(app, community)

        async def exec_test():
            await explorer_graph._explore(self.idB, 5)
            self.assertEqual(len(explorer_graph.nx_graph.nodes()), 5)
            self.assertEqual(len(explorer_graph.nx_graph.edges()), 4)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_explore_full_from_extremity(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        explorer_graph = ExplorerGraph(app, community)

        async def exec_test():
            await explorer_graph._explore(self.idA, 5)
            self.assertEqual(len(explorer_graph.nx_graph.nodes()), 5)
            self.assertEqual(len(explorer_graph.nx_graph.edges()), 4)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_explore_partial(self, app, community):
        community.parameters = CoroutineMock(return_value = {'sigValidity': 1000})
        community.network.confirmations = Mock(side_effect=lambda n: 4 if 996 else None)
        app.preferences = {'expert_mode': True}

        explorer_graph = ExplorerGraph(app, community)

        async def exec_test():
            await explorer_graph._explore(self.idB, 1)
            self.assertEqual(len(explorer_graph.nx_graph.nodes()), 3)
            self.assertEqual(len(explorer_graph.nx_graph.edges()), 2)

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    @patch('time.time', Mock(return_value=50000))
    def test_start_stop_exploration(self, app, community):
        async def explore_mock(id, steps):
            await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)

        explorer_graph = ExplorerGraph(app, community)
        explorer_graph._explore = explore_mock

        async def exec_test():
            self.assertEqual(explorer_graph.exploration_task, None)
            explorer_graph.start_exploration(self.idA, 1)
            self.assertNotEqual(explorer_graph.exploration_task, None)
            task = explorer_graph.exploration_task
            explorer_graph.start_exploration(self.idA, 1)
            self.assertEqual(task, explorer_graph.exploration_task)
            explorer_graph.start_exploration(self.idB, 1)
            await asyncio.sleep(0)
            self.assertTrue(task.cancelled())
            self.assertNotEqual(task, explorer_graph.exploration_task)
            task2 = explorer_graph.exploration_task
            explorer_graph.start_exploration(self.idB, 2)
            await asyncio.sleep(0)
            self.assertTrue(task2.cancelled())
            task3 = explorer_graph.exploration_task
            explorer_graph.stop_exploration()
            await asyncio.sleep(0)
            self.assertTrue(task2.cancelled())


        self.lp.run_until_complete(exec_test())
