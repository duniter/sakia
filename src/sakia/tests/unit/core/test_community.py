import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.core.net.api.bma.access import BmaAccess
from sakia.core.net.network import Network
from sakia.core import Community
from sakia.tests import QuamashTest


class TestCommunity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

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
