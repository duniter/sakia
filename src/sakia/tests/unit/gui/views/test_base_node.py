import unittest
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.gui.views.nodes.base_node import BaseNode
from sakia.core.graph.constants import NodeStatus


class TestBaseNode(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_create_edge(self):
        metadata = {
            'status': NodeStatus.NEUTRAL,
            'text': "UserA",
            'tooltip': "TestTooltip"
        }
        nx_pos = {
            "A": (0, 5),
            "B": (10, 20)
        }
        async def exec_test():
            node = BaseNode(("A", metadata), nx_pos)
            self.assertEqual(node.id, "A")
            self.assertEqual(node.metadata['status'], NodeStatus.NEUTRAL)
            self.assertEqual(node.x, 0)
            self.assertEqual(node.y, 5)
            self.assertEqual(node.status_wallet, False)
            self.assertEqual(node.status_member, True)
            self.assertEqual(node.text, "UserA")
            self.assertEqual(node.toolTip(), "TestTooltip")

        self.lp.run_until_complete(exec_test())