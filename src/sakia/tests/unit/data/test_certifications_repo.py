from sakia.data.repositories import CertificationsRepo, SakiaDatabase
from sakia.data.entities import Certification
from duniterpy.documents import BlockUID
import unittest
import sqlite3


class TestCertificationsRepo(unittest.TestCase):
    def setUp(self):
        self.meta_repo = SakiaDatabase(sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES))
        self.meta_repo.prepare()
        self.meta_repo.upgrade_database()

    def tearDown(self):
        pass

    def test_add_get_drop_blockchain(self):
        certifications_repo = CertificationsRepo(self.meta_repo.conn)
        certifications_repo.insert(Certification("testcurrency",
                                                 "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                 "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                                 20,
                                                 1473108382,
                                                 "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                                 None))
        certification = certifications_repo.get_one(currency="testcurrency",
                                                    certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                    certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                                    block=20)
        self.assertEqual(certification.currency, "testcurrency")
        self.assertEqual(certification.certifier, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(certification.certified, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
        self.assertEqual(certification.block, 20)
        self.assertEqual(certification.timestamp, 1473108382)
        self.assertEqual(certification.signature, "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==")
        self.assertEqual(certification.written_on, BlockUID.empty())
        certifications_repo.drop(certification)
        certification = certifications_repo.get_one(currency="testcurrency",
                                           certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                           block=20)
        self.assertIsNone(certification)

    def test_add_get_multiple_certification(self):
        certifications_repo = CertificationsRepo(self.meta_repo.conn)
        certifications_repo.insert(Certification("testcurrency",
                                                 "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                 "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                                 20, 1473108382,
                                                 "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                                 "22-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        certifications_repo.insert(Certification("testcurrency",
                                                 "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                                 "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                 101, 1473108382,
                                                 "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                                 "105-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        certifications = certifications_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [i.currency for i in certifications])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [i.certifier for i in certifications])
        self.assertIn("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", [i.certifier for i in certifications])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [i.certified for i in certifications])
        self.assertIn("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", [i.certified for i in certifications])

    def test_add_update_certification(self):
        certifications_repo = CertificationsRepo(self.meta_repo.conn)
        certification = Certification("testcurrency",
                                 "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                 "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                 "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                 1473108382,
                                 "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                 None)

        certifications_repo.insert(certification)
        certification.written_on = BlockUID(22, "148C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        certifications_repo.update(certification)
        cert2 = certifications_repo.get_one(currency="testcurrency",
                                            certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                            certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                            block=20)
        self.assertTrue(cert2.written_on)
