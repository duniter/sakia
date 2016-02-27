import unittest
from unittest.mock import Mock
import time
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import Identity, IdentitiesRegistry, LocalState, BlockchainState

from sakia.tests.mocks.bma import nice_blockchain, corrupted
from sakia.tests import QuamashTest
from sakia.core import Application, Community
from sakia.core.net import Network, Node
from ucoinpy.documents.peer import Peer
from sakia.core.net.api.bma.access import BmaAccess


class TestBmaAccess(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.peer = Peer.from_signed_raw("""Version: 2
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API ucoin.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
        self.node = Node(self.peer,
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.12.0", 0, Mock("aiohttp.ClientSession"))
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
