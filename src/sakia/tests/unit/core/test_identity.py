import unittest
from asynctest import Mock, CoroutineMock
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import Identity, LocalState, BlockchainState

from sakia.tests.mocks.bma import nice_blockchain, corrupted
from sakia.tests import QuamashTest
from ucoinpy.api import bma
from ucoinpy.documents import BlockUID
from sakia.tools.exceptions import MembershipNotFoundError


class TestIdentity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = Mock(spec='sakia.core.registry.IdentitiesRegistry')
        self.community = Mock(spec='sakia.core.Community')
        self.community.name = "test_brouzouf"
        self.community.bma_access = Mock(spec='sakia.core.net.api.bma.BmaAccess')

    def tearDown(self):
        self.tearDownQuamash()

    def test_identity_certifiers_of(self):
        def bma_access(request, *args):
            if request is bma.wot.CertifiersOf:
                return nice_blockchain.bma_certifiers_of_john
            if request is bma.wot.Lookup:
                return nice_blockchain.bma_lookup_john
            if request is bma.blockchain.Block:
                return nice_blockchain.bma_blockchain_current

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                            BlockUID(20, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"),
                            LocalState.COMPLETED, BlockchainState.VALIDATED)
        id_doe = Identity("doe", "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                            BlockUID(101, "BAD49448A1AD73C978CEDCB8F137D20A5715EBAA739DAEF76B1E28EE67B2C00C"),
                            LocalState.COMPLETED, BlockchainState.VALIDATED)

        self.community.bma_access.future_request = CoroutineMock(side_effect=bma_access)
        self.identities_registry.from_handled_data = Mock(return_value=id_doe)
        async def exec_test():
            certifiers = await identity.certifiers_of(self.identities_registry, self.community)

            self.assertEqual(len(certifiers), 2)
            self.assertEqual(certifiers[0]['identity'].uid, "doe")
            self.assertEqual(certifiers[1]['identity'].uid, "doe")

        self.lp.run_until_complete(exec_test())

    def test_identity_membership(self):
        def bma_access(request, *args):
            if request is bma.blockchain.Membership:
                return nice_blockchain.bma_membership_john

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                            BlockUID(20, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"),
                            LocalState.COMPLETED, BlockchainState.VALIDATED)

        self.community.bma_access.future_request = CoroutineMock(side_effect=bma_access)

        async def exec_test():
            ms = await identity.membership(self.community)
            self.assertEqual(ms["blockNumber"], 0)
            self.assertEqual(ms["blockHash"], "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855")
            self.assertEqual(ms["membership"], "IN")
            self.assertEqual(ms["currency"], "test_currency")
            self.assertEqual(ms["written"], 10000)

        self.lp.run_until_complete(exec_test())

    def test_identity_corrupted_membership(self):
        def bma_access(request, *args):
            if request is bma.blockchain.Membership:
                return corrupted.bma_memberships_empty_array

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                            BlockUID(20, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"),
                            LocalState.COMPLETED, BlockchainState.VALIDATED)
        self.community.bma_access.future_request = CoroutineMock(side_effect=bma_access)
        async def exec_test():
            with self.assertRaises(MembershipNotFoundError):
                await identity.membership(self.community)

        self.lp.run_until_complete(exec_test())

