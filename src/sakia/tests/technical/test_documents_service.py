import asyncio
import unittest
import sqlite3
import aiohttp
from duniterpy.documents import BlockUID, Peer
from sakia.tests import QuamashTest
from sakia.services import DocumentsService
from sakia.data.connectors import NodeConnector, BmaConnector
from sakia.data.repositories import NodesRepo, SakiaDatabase, BlockchainsRepo, IdentitiesRepo
from sakia.data.processors import NodesProcessor, BlockchainProcessor, IdentitiesProcessor


class TestDocumentsService(unittest.TestCase, QuamashTest):
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

    def test_certify(self):
        meta_repo = SakiaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        nodes_repo = NodesRepo(self.con)
        nodes_processor = NodesProcessor(nodes_repo)
        bma_connector = BmaConnector(nodes_processor)
        blockchain_repo = BlockchainsRepo(self.con)
        identities_repo = IdentitiesRepo(self.con)
        blockchain_processor = BlockchainProcessor(blockchain_repo, bma_connector)
        identities_processor = IdentitiesProcessor(identities_repo, bma_connector)
        documents_service = DocumentsService(bma_connector, blockchain_processor, identities_processor)
        #TODO: Build a framework to test documents broadcasting

