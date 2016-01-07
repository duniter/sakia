import unittest
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.gui.views.edges.base_edge import BaseEdge
from sakia.core.graph.constants import EdgeStatus


class TestBaseEdge(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_create_edge(self):
        metadata = {
            'status': EdgeStatus.STRONG
        }
        nx_pos = {
            "A": (0, 5),
            "B": (10, 20)
        }
        async def exec_test():
            edge = BaseEdge("A", "B", metadata, nx_pos)
            self.assertEqual(edge.source, "A")
            self.assertEqual(edge.destination, "B")
            self.assertEqual(edge.destination_point.x(), 10)
            self.assertEqual(edge.destination_point.y(), 20)
            self.assertEqual(edge.source_point.x(), 0)
            self.assertEqual(edge.source_point.y(), 5)
            self.assertEqual(edge.status, EdgeStatus.STRONG)

        self.lp.run_until_complete(exec_test())