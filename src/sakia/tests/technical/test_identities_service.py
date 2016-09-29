import unittest
import sqlite3
from duniterpy.documents import BlockUID, Block
from sakia.tests.mocks.bma.nice_blockchain import bma_blockchain_0
from sakia.tests import QuamashTest
from sakia.services import IdentitiesService
from sakia.data.repositories import CertificationsRepo, IdentitiesRepo, MetaDatabase
from sakia.data.processors import CertificationsProcessor, IdentitiesProcessor


class TestIdentitiesService(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_adapter(list, lambda ls: '\n'.join([str(v) for v in ls]))
        sqlite3.register_adapter(tuple, lambda ls: '\n'.join([str(v) for v in ls]))
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.tearDownQuamash()

    def test_new_block_with_unknown_identities(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        identities_repo = IdentitiesRepo(self.con)
        certs_repo = CertificationsRepo(self.con)
        identities_processor = IdentitiesProcessor("testcurrency", identities_repo, None)
        certs_processor = CertificationsProcessor("testcurrency", certs_repo, None)
        identities_service = IdentitiesService("testcurrency", identities_processor, certs_processor, None)
        block = Block.from_signed_raw("{0}{1}\n".format(bma_blockchain_0["raw"], bma_blockchain_0["signature"]))
        identities_service.parse_block(block)
        self.assertEqual(identities_processor.get_written("8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"), [])
        self.assertEqual(identities_processor.get_written("HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"), [])
        self.assertEqual(identities_processor.get_written("BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH"), [])
        self.assertEqual(identities_processor.get_written("37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw"), [])
