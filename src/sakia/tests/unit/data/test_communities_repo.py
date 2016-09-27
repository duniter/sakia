import sqlite3
import unittest

from duniterpy.documents import BlockUID

from sakia.data.entities import Community
from sakia.data.repositories import CommunitiesRepo, MetaDatabase


class TestCommunitiesRepo(unittest.TestCase):
    def setUp(self):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.con.close()

    def test_add_get_drop_community(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        communities_repo = CommunitiesRepo(self.con)
        communities_repo.insert(Community(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66,
            "testcurrency"
        ))
        community = communities_repo.get_one(currency="testcurrency")
        self.assertEqual(community.currency, "testcurrency")
        self.assertEqual(community.c, 0.1)
        self.assertEqual(community.dt, 86400)

        communities_repo.drop(community)
        community = communities_repo.get_one(currency="testcurrency")
        self.assertIsNone(community)

    def test_add_get_multiple_community(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        communities_repo = CommunitiesRepo(self.con)
        communities_repo.insert(Community(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66,
            "testcurrency"
        )
        )
        communities_repo.insert(Community(
            0.1,
            86400 * 365,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66,
            "testcurrency2"
        )
        )
        communities = communities_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [i.currency for i in communities])
        self.assertIn("testcurrency2", [i.currency for i in communities])
        self.assertIn(86400, [i.dt for i in communities])
        self.assertIn(86400 * 365, [i.dt for i in communities])

    def test_add_update_community(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        communities_repo = CommunitiesRepo(self.con)
        community = Community(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66,
            "testcurrency"
        )
        communities_repo.insert(community)
        community.c = 0.0922
        communities_repo.update(community)
        community2 = communities_repo.get_one(currency="testcurrency")
        self.assertEquals(0.0922, community2.c)
