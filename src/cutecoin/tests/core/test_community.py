import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.core.net.api.bma.access import BmaAccess
from cutecoin.core.net.network import Network
from cutecoin.core import Community
from cutecoin.tests import get_application


class TestCommunity(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_load_save_community(self):
        network = Network("test_currency", [])
        bma_access = BmaAccess([], network)
        community = Community("test_currency", network, bma_access)

        json_data = community.jsonify()
        community_from_json = Community.load(json_data)
        self.assertEqual(community.name, community_from_json.name)
        self.assertEqual(len(community.network._nodes), len(community_from_json.network._nodes))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
