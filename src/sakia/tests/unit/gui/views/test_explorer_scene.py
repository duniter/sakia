import unittest
import networkx
import math
from unittest.mock import patch, Mock
from sakia.tests import QuamashTest
from sakia.gui.views.scenes import ExplorerScene
from sakia.core.graph.constants import NodeStatus


class TestExplorerScene(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        self.identities_uids = ['A', 'B', 'C', 'D', 'E']
        self.identities_pubkeys = ['pbkA', 'pbkB', 'pbkC', 'pbkD', 'pbkE']
        self.certifications = [('pbkA', 'pbkB'),
                               ('pbkB', 'pbkC'),
                               ('pbkD', 'pbkA'),
                               ('pbkA', 'pbkE')]
        # Graph :
        #  A -> B -> C
        #    <- D
        #    -> E
        self.identity_status = [NodeStatus.SELECTED, NodeStatus.NEUTRAL, NodeStatus.NEUTRAL,
                                NodeStatus.OUT, NodeStatus.NEUTRAL]
        self.test_graph = networkx.MultiDiGraph().to_undirected()
        self.test_graph.add_nodes_from(self.identities_pubkeys)
        self.test_graph.add_edges_from(self.certifications)
        for index, node in enumerate(self.test_graph.nodes(data=True)):
            node[1]['text'] = self.identities_uids[index]
            node[1]['tooltip'] = self.identities_pubkeys[index]
            node[1]['status'] = self.identity_status[index]

    def tearDown(self):
        self.tearDownQuamash()

    def test_init_layout(self):
        data_layout = ExplorerScene._init_layout(self.test_graph)
        for pubkey in self.identities_pubkeys:
            self.assertEqual(data_layout[pubkey]['theta'], None)
            self.assertEqual(data_layout[pubkey]['scenter'], 25)
            self.assertEqual(data_layout[pubkey]['nchild'], 0)
            self.assertEqual(data_layout[pubkey]['sparent'], None)
            self.assertEqual(data_layout[pubkey]['stsize'], 0.0)
            self.assertEqual(data_layout[pubkey]['span'], 0.0)

    def test_set_parent_nodes(self):
        data_layout = ExplorerScene._init_layout(self.test_graph)
        ExplorerScene._set_parent_nodes(self.test_graph, data_layout, 'pbkA')
        self.assertEqual(data_layout['pbkA']['scenter'], 0)
        self.assertEqual(data_layout['pbkB']['scenter'], 1)
        self.assertEqual(data_layout['pbkC']['scenter'], 2)
        self.assertEqual(data_layout['pbkD']['scenter'], 1)
        self.assertEqual(data_layout['pbkE']['scenter'], 1)

        self.assertEqual(data_layout['pbkA']['sparent'], None)
        self.assertEqual(data_layout['pbkB']['sparent'], 'pbkA')
        self.assertEqual(data_layout['pbkC']['sparent'], 'pbkB')
        self.assertEqual(data_layout['pbkD']['sparent'], 'pbkA')
        self.assertEqual(data_layout['pbkE']['scenter'], 1)

        self.assertEqual(data_layout['pbkA']['nchild'], 3)
        self.assertEqual(data_layout['pbkB']['nchild'], 1)
        self.assertEqual(data_layout['pbkC']['nchild'], 0)
        self.assertEqual(data_layout['pbkD']['nchild'], 0)
        self.assertEqual(data_layout['pbkE']['nchild'], 0)

    def test_set_subtree_size(self):
        data_layout = ExplorerScene._init_layout(self.test_graph)

        data_layout['pbkA']['sparent'] = None
        data_layout['pbkB']['sparent'] = 'pbkA'
        data_layout['pbkC']['sparent'] = 'pbkB'
        data_layout['pbkD']['sparent'] = 'pbkA'
        data_layout['pbkE']['sparent'] = 'pbkA'

        data_layout['pbkA']['nchild'] = 2
        data_layout['pbkB']['nchild'] = 1
        data_layout['pbkC']['nchild'] = 0
        data_layout['pbkD']['nchild'] = 0
        data_layout['pbkE']['nchild'] = 0

        ExplorerScene._set_subtree_size(self.test_graph, data_layout)
        self.assertAlmostEqual(data_layout['pbkA']['stsize'], 3.0)
        self.assertAlmostEqual(data_layout['pbkB']['stsize'], 1.0)
        self.assertAlmostEqual(data_layout['pbkC']['stsize'], 1.0)
        self.assertAlmostEqual(data_layout['pbkD']['stsize'], 1.0)
        self.assertAlmostEqual(data_layout['pbkE']['stsize'], 1.0)

    def test_set_subtree_span(self):
        data_layout = ExplorerScene._init_layout(self.test_graph)

        data_layout['pbkA']['sparent'] = None
        data_layout['pbkB']['sparent'] = 'pbkA'
        data_layout['pbkC']['sparent'] = 'pbkB'
        data_layout['pbkD']['sparent'] = 'pbkA'
        data_layout['pbkE']['sparent'] = 'pbkA'

        data_layout['pbkA']['nchild'] = 2
        data_layout['pbkB']['nchild'] = 1
        data_layout['pbkC']['nchild'] = 0
        data_layout['pbkD']['nchild'] = 0
        data_layout['pbkE']['nchild'] = 0

        data_layout['pbkA']['stsize'] = 3.0
        data_layout['pbkB']['stsize'] = 1.0
        data_layout['pbkC']['stsize'] = 1.0
        data_layout['pbkD']['stsize'] = 1.0
        data_layout['pbkE']['stsize'] = 1.0

        data_layout['pbkA']['span'] = 2 * math.pi

        ExplorerScene._set_subtree_spans(self.test_graph, data_layout, 'pbkA')
        self.assertAlmostEqual(data_layout['pbkA']['span'], 2 * math.pi)
        self.assertAlmostEqual(data_layout['pbkB']['span'], 2 / 3 * math.pi)
        self.assertAlmostEqual(data_layout['pbkC']['span'], 2 / 3 * math.pi)
        self.assertAlmostEqual(data_layout['pbkD']['span'], 2 / 3 * math.pi)
        self.assertAlmostEqual(data_layout['pbkE']['span'], 2 / 3 * math.pi)

    @patch('networkx.MultiDiGraph')
    def test_set_subtree_position(self, mock_graph):
        # We mock the edges generator to ensure the order in which they appear
        mock_graph.edges = Mock(return_value=self.certifications)
        data_layout = {}

        for pubkey in self.identities_pubkeys:
            data_layout[pubkey] = {
                'theta': None
            }

        data_layout['pbkA']['sparent'] = None
        data_layout['pbkB']['sparent'] = 'pbkA'
        data_layout['pbkC']['sparent'] = 'pbkB'
        data_layout['pbkD']['sparent'] = 'pbkA'
        data_layout['pbkE']['sparent'] = 'pbkA'

        data_layout['pbkA']['nchild'] = 2
        data_layout['pbkB']['nchild'] = 1
        data_layout['pbkC']['nchild'] = 0
        data_layout['pbkD']['nchild'] = 0
        data_layout['pbkE']['nchild'] = 0

        data_layout['pbkA']['span'] = 2 * math.pi
        data_layout['pbkB']['span'] = 2 / 3 * math.pi
        data_layout['pbkC']['span'] = 2 / 3 * math.pi
        data_layout['pbkD']['span'] = 2 / 3 * math.pi
        data_layout['pbkE']['span'] = 2 / 3 * math.pi

        data_layout['pbkA']['theta'] = 0.0
        ExplorerScene._set_positions(mock_graph, data_layout, 'pbkA')
        self.assertAlmostEqual(data_layout['pbkA']['theta'], 0.0)
        self.assertAlmostEqual(data_layout['pbkB']['theta'], 1 / 3 * math.pi)
        self.assertAlmostEqual(data_layout['pbkC']['theta'], 1 / 3 * math.pi)
        self.assertAlmostEqual(data_layout['pbkD']['theta'], math.pi)
        self.assertAlmostEqual(data_layout['pbkE']['theta'], 5 / 3 * math.pi)

    @patch('networkx.MultiDiGraph')
    @patch('networkx.MultiGraph')
    @patch('networkx.shortest_path_length', return_value={'pbkA': 0, 'pbkB': 1, 'pbkC': 2, 'pbkD': 1, 'pbkE': 1})
    def test_twopi_layout(self, mock_graph, mock_undirected, mock_paths):
        # We mock the edges generator to ensure the order in which they appear
        mock_graph.edges = Mock(return_value=self.certifications)
        mock_graph.nodes = Mock(return_value=self.identities_pubkeys)
        mock_graph.to_undirected = Mock(return_value=mock_undirected)
        mock_undirected.nodes = Mock(return_value=self.identities_pubkeys)
        mock_undirected.edges = Mock(return_value=self.certifications)

        pos = ExplorerScene.twopi_layout(mock_graph, 'pbkA')

        self.assertAlmostEqual(pos['pbkA'][0], 1 * math.cos(0.0) * 50)
        self.assertAlmostEqual(pos['pbkB'][0], 2 * math.cos(1 / 3 * math.pi) * 50)
        self.assertAlmostEqual(pos['pbkC'][0], 3 * math.cos(1 / 3 * math.pi) * 50)
        self.assertAlmostEqual(pos['pbkD'][0], 2 * math.cos(math.pi) * 50)
        self.assertAlmostEqual(pos['pbkE'][0], 2 * math.cos(5 / 3 * math.pi) * 50)

        self.assertAlmostEqual(pos['pbkA'][1], 1 * math.sin(0.0) * 50)
        self.assertAlmostEqual(pos['pbkB'][1], 2 * math.sin(1 / 3 * math.pi) * 50)
        self.assertAlmostEqual(pos['pbkC'][1], 3 * math.sin(1 / 3 * math.pi) * 50)
        self.assertAlmostEqual(pos['pbkD'][1], 2 * math.sin(math.pi) * 50)
        self.assertAlmostEqual(pos['pbkE'][1], 2 * math.sin(5 / 3 * math.pi) * 50)