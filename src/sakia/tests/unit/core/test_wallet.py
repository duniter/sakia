import unittest
import pypeg2
from unittest.mock import MagicMock, PropertyMock
from asynctest import CoroutineMock
from duniterpy.grammars import output
from duniterpy.documents import BlockUID
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.core import Wallet
from sakia.tests import QuamashTest


class TestWallet(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry({})

    def tearDown(self):
        self.tearDownQuamash()

    def test_load_save_wallet(self):
        wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        json_data = wallet.jsonify()
        wallet_from_json = Wallet.load(json_data, self.identities_registry)
        self.assertEqual(wallet.walletid, wallet_from_json.walletid)
        self.assertEqual(wallet.pubkey, wallet_from_json.pubkey)
        self.assertEqual(wallet.name, wallet_from_json.name)
        self.assertEqual(wallet._identities_registry, wallet_from_json._identities_registry)

    def test_prepare_tx_base_0(self):
        community = MagicMock("sakia.core.Community")
        community.currency = "test_currency"
        cache = MagicMock("sakia.core.txhistory.TxHistory")
        cache.available_sources = [{
            "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
            "type": "D",
            "noffset": 2,
            "identifier": "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
            "amount": 15,
            "base": 0
        },
            {
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "noffset": 4,
                "identifier": "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                "amount": 85,
                "base": 0
            },
            {
                "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                "type": "T",
                "noffset": 4,
                "identifier": "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                "amount": 11,
                "base": 1
            }]
        wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                        "Wallet 1", self.identities_registry)
        wallet.caches["test_currency"] = cache
        tx = wallet.prepare_tx("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               BlockUID(32, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8"),
                               99, "", community)
        self.assertEqual(tx.version, 3)
        self.assertEqual(tx.blockstamp.number, 32)
        self.assertEqual(tx.blockstamp.sha_hash, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8")
        self.assertEqual(len(tx.issuers), 1)
        self.assertEqual(tx.issuers[0], "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(len(tx.inputs), 2)
        self.assertEqual(tx.inputs[0].origin_id, "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertEqual(tx.inputs[0].source, "D")
        self.assertEqual(tx.inputs[0].index, 2)
        self.assertEqual(tx.inputs[1].origin_id, "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5")
        self.assertEqual(tx.inputs[1].source, "D")
        self.assertEqual(tx.inputs[1].index, 4)
        self.assertEqual(len(tx.outputs), 2)
        self.assertEqual(tx.outputs[0].amount, 99)
        self.assertEqual(tx.outputs[0].base, 0)
        self.assertEqual(pypeg2.compose(tx.outputs[0].conditions, output.Condition),
                         "SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)")
        self.assertEqual(tx.outputs[1].amount, 1)
        self.assertEqual(tx.outputs[1].base, 0)
        self.assertEqual(pypeg2.compose(tx.outputs[1].conditions, output.Condition),
                         "SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)")
        self.assertEqual(len(tx.unlocks), 2)
        self.assertEqual(tx.unlocks[0].index, 0)
        self.assertEqual(tx.unlocks[0].parameters[0].index, 0)
        self.assertEqual(tx.unlocks[1].index, 1)
        self.assertEqual(tx.unlocks[0].parameters[0].index, 0)

    def test_prepare_tx_base_1(self):
        community = MagicMock("sakia.core.Community")
        community.currency = "test_currency"
        cache = MagicMock("sakia.core.txhistory.TxHistory")
        cache.available_sources = [{
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "noffset": 2,
                "identifier": "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                "amount": 15,
                "base": 0
            },
            {
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "noffset": 4,
                "identifier": "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                "amount": 85,
                "base": 0
            },
            {
                "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                "type": "T",
                "noffset": 4,
                "identifier": "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                "amount": 11,
                "base": 1
            }]
        wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)
        wallet.caches["test_currency"] = cache
        tx = wallet.prepare_tx("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               BlockUID(32, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8"),
                               100, "", community)
        self.assertEqual(tx.version, 3)
        self.assertEqual(tx.blockstamp.number, 32)
        self.assertEqual(tx.blockstamp.sha_hash, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8")
        self.assertEqual(len(tx.issuers), 1)
        self.assertEqual(tx.issuers[0], "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(len(tx.inputs), 1)
        self.assertEqual(tx.inputs[0].origin_id, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        self.assertEqual(tx.inputs[0].source, "T")
        self.assertEqual(tx.inputs[0].index, 4)
        self.assertEqual(len(tx.outputs), 2)
        self.assertEqual(tx.outputs[0].amount, 10)
        self.assertEqual(tx.outputs[0].base, 1)
        self.assertEqual(pypeg2.compose(tx.outputs[0].conditions, output.Condition),
                         "SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)")
        self.assertEqual(tx.outputs[1].amount, 1)
        self.assertEqual(tx.outputs[1].base, 1)
        self.assertEqual(pypeg2.compose(tx.outputs[1].conditions, output.Condition),
                         "SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)")
        self.assertEqual(len(tx.unlocks), 1)
        self.assertEqual(tx.unlocks[0].index, 0)
        self.assertEqual(tx.unlocks[0].parameters[0].index, 0)

    def test_prepare_tx_base_1_overheads(self):
        community = MagicMock("sakia.core.Community")
        community.currency = "test_currency"
        cache = MagicMock("sakia.core.txhistory.TxHistory")
        cache.available_sources = [{
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "noffset": 2,
                "identifier": "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                "amount": 15,
                "base": 0
            },
            {
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "noffset": 4,
                "identifier": "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                "amount": 85,
                "base": 0
            },
            {
                "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                "type": "T",
                "noffset": 4,
                "identifier": "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                "amount": 11,
                "base": 1
            }]
        wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)
        wallet.caches["test_currency"] = cache
        tx = wallet.prepare_tx("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               BlockUID(32, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8"),
                               101, "", community)
        self.assertEqual(tx.version, 3)
        self.assertEqual(tx.blockstamp.number, 32)
        self.assertEqual(tx.blockstamp.sha_hash, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8")
        self.assertEqual(len(tx.issuers), 1)
        self.assertEqual(tx.issuers[0], "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(len(tx.inputs), 2)
        self.assertEqual(tx.inputs[0].origin_id, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        self.assertEqual(tx.inputs[0].source, "T")
        self.assertEqual(tx.inputs[0].index, 4)
        self.assertEqual(tx.inputs[1].origin_id, "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertEqual(tx.inputs[1].source, "D")
        self.assertEqual(tx.inputs[1].index, 2)
        self.assertEqual(len(tx.outputs), 4)
        self.assertEqual(tx.outputs[0].amount, 1)
        self.assertEqual(tx.outputs[0].base, 0)
        self.assertEqual(pypeg2.compose(tx.outputs[0].conditions, output.Condition),
                         "SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)")
        self.assertEqual(tx.outputs[1].amount, 10)
        self.assertEqual(tx.outputs[1].base, 1)
        self.assertEqual(pypeg2.compose(tx.outputs[1].conditions, output.Condition),
                         "SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)")
        self.assertEqual(tx.outputs[2].amount, 14)
        self.assertEqual(tx.outputs[2].base, 0)
        self.assertEqual(pypeg2.compose(tx.outputs[2].conditions, output.Condition),
                         "SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)")
        self.assertEqual(tx.outputs[3].amount, 1)
        self.assertEqual(tx.outputs[3].base, 1)
        self.assertEqual(pypeg2.compose(tx.outputs[3].conditions, output.Condition),
                         "SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)")
        self.assertEqual(len(tx.unlocks), 2)
        self.assertEqual(tx.unlocks[0].index, 0)
        self.assertEqual(tx.unlocks[0].parameters[0].index, 0)
        self.assertEqual(tx.unlocks[1].index, 1)
        self.assertEqual(tx.unlocks[1].parameters[0].index, 0)
