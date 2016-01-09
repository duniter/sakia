import unittest
from unittest.mock import patch
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.gui.views.edges import ExplorerEdge
from sakia.core.graph.constants import EdgeStatus


class TestExplorerEdge(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_create_wot_edge(self):
        metadata = {
            'status': EdgeStatus.STRONG,
            'confirmation_text': "0/6"
        }
        nx_pos = {
            "A": (0, 5),
            "B": (10, 20)
        }
        async def exec_test():
            edge = ExplorerEdge("A", "B", metadata, nx_pos, 0, 0)
            self.assertEqual(edge.source, "A")
            self.assertEqual(edge.destination, "B")
            self.assertAlmostEqual(edge.destination_point.x(), 10.0, delta=5)
            self.assertAlmostEqual(edge.destination_point.y(), 20.0, delta=5)
            self.assertAlmostEqual(edge.source_point.x(), 10.0, delta=5)
            self.assertAlmostEqual(edge.source_point.y(), 20.0, delta=5)
            self.assertEqual(edge.status, EdgeStatus.STRONG)

        self.lp.run_until_complete(exec_test())

    @patch('PyQt5.QtGui.QPainter')
    @patch('PyQt5.QtWidgets.QWidget')
    def test_paint(self, painter, widget):
        metadata = {
            'status': EdgeStatus.STRONG,
            'confirmation_text': "0/6"
        }
        nx_pos = {
            "A": (0, 5),
            "B": (10, 20)
        }

        async def exec_test():
            edge = ExplorerEdge("A", "B", metadata, nx_pos, 0, 1)
            edge.paint(painter, 0, widget)

        self.lp.run_until_complete(exec_test())

    @patch('PyQt5.QtGui.QPainter')
    @patch('PyQt5.QtWidgets.QWidget')
    def test_bounding_rect(self, painter, widget):
        metadata = {
            'status': EdgeStatus.STRONG,
            'confirmation_text': "0/6"
        }
        nx_pos = {
            "A": (0, 5),
            "B": (10, 20)
        }

        async def exec_test():
            edge = ExplorerEdge("A", "B", metadata, nx_pos, 0, 0)
            bounding_rect = edge.boundingRect()
            self.assertAlmostEqual(bounding_rect.x(), 7.0, delta=5)
            self.assertAlmostEqual(bounding_rect.y(), 17.0, delta=5)
            self.assertAlmostEqual(bounding_rect.width(), 6.0, delta=5)
            self.assertAlmostEqual(bounding_rect.height(), 6.0, delta=5)

        self.lp.run_until_complete(exec_test())
