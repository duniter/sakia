from sakia.data.repositories import CertificationsRepo
from sakia.data.entities import Certification


def test_add_get_drop_blockchain(meta_repo):
    certifications_repo = CertificationsRepo(meta_repo.conn)
    certifications_repo.insert(Certification("testcurrency",
                                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                             "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                             20,
                                             1473108382,
                                             "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                             0))
    certification = certifications_repo.get_one(currency="testcurrency",
                                                certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                                block=20)
    assert certification.currency == "testcurrency"
    assert certification.certifier == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert certification.certified == "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
    assert certification.block == 20
    assert certification.timestamp == 1473108382
    assert certification.signature == "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw=="
    assert certification.written_on == 0
    certifications_repo.drop(certification)
    certification = certifications_repo.get_one(currency="testcurrency",
                                       certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                       certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                       block=20)
    assert certification is None


def test_add_get_multiple_certification(meta_repo):
    certifications_repo = CertificationsRepo(meta_repo.conn)
    certifications_repo.insert(Certification("testcurrency",
                                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                             "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                             20, 1473108382,
                                             "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                             22))
    certifications_repo.insert(Certification("testcurrency",
                                             "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                             101, 1473108382,
                                             "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                             105))
    certifications = certifications_repo.get_all(currency="testcurrency")
    assert "testcurrency" in [i.currency for i in certifications]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in [i.certifier for i in certifications]
    assert "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ" in [i.certifier for i in certifications]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in [i.certified for i in certifications]
    assert "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ" in [i.certified for i in certifications]


def test_add_update_certification(meta_repo):
    certifications_repo = CertificationsRepo(meta_repo.conn)
    certification = Certification("testcurrency",
                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                             20,
                             1473108382,
                             "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                             0)

    certifications_repo.insert(certification)
    certification.written_on = 22
    certifications_repo.update(certification)
    cert2 = certifications_repo.get_one(currency="testcurrency",
                                        certifier="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                        certified="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                        block=20)
    assert cert2.written_on == 22

