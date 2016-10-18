from sakia.data.repositories import SourcesRepo, SakiaDatabase
from sakia.data.entities import Source
from duniterpy.documents import BlockUID
import unittest
import sqlite3


class TestSourcesRepo(unittest.TestCase):
    def setUp(self):
        self.meta_repo = SakiaDatabase(sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES))
        self.meta_repo.prepare()
        self.meta_repo.upgrade_database()

    def tearDown(self):
        pass

    def test_add_get_drop_source(self):
        sources_repo = SourcesRepo(self.meta_repo.conn)
        sources_repo.insert(Source("0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843",
                                   "testcurrency",
                                   "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                   "T",
                                   3,
                                   1565,
                                   1))
        source = sources_repo.get_one(identifier="0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843")
        self.assertEqual(source.currency, "testcurrency")
        self.assertEqual(source.pubkey, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
        self.assertEqual(source.type, "T")
        self.assertEqual(source.amount, 1565)
        self.assertEqual(source.base, 1)
        self.assertEqual(source.offset, 3)

        sources_repo.drop(source)
        source = sources_repo.get_one(identifier="0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843")
        self.assertIsNone(source)

    def test_add_get_multiple_source(self):
        sources_repo = SourcesRepo(self.meta_repo.conn)
        sources_repo.insert(Source("0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843",
                                   "testcurrency",
                                   "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                   "T",
                                   3,
                                   1565,
                                   1))
        sources_repo.insert(Source("2pyPsXM8UCB88jP2NRM4rUHxb63qm89JMEWbpoRrhyDK",
                                   "testcurrency",
                                   "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                   "D",
                                   22635,
                                   726946,
                                   1))
        sources = sources_repo.get_all(currency="testcurrency", pubkey="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
        self.assertIn("testcurrency", [s.currency for s in sources])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [s.pubkey for s in sources])
        self.assertIn("2pyPsXM8UCB88jP2NRM4rUHxb63qm89JMEWbpoRrhyDK", [s.identifier for s in sources])
        self.assertIn("T", [s.type for s in sources])
        self.assertIn("D", [s.type for s in sources])
        self.assertIn(726946, [s.amount for s in sources])
        self.assertIn(1565, [s.amount for s in sources])
        self.assertIn("0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843", [s.identifier for s in sources])
