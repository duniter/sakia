from sakia.data.repositories import IdentitiesRepo
from sakia.data.entities import Identity
from duniterpy.documents import BlockUID


def test_add_get_drop_identity(meta_repo):
    identities_repo = IdentitiesRepo(meta_repo.conn)
    identities_repo.insert(Identity("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                    "john",
                                    "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                    "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                    1473108382))
    identity = identities_repo.get_one(currency="testcurrency",
                                       pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                       uid="john",
                                       blockstamp=BlockUID(20,
                                                "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                                       )
    assert identity.currency == "testcurrency"
    assert identity.pubkey == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert identity.uid == "john"
    assert identity.blockstamp.number == 20
    assert identity.blockstamp.sha_hash == "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"
    assert identity.timestamp == 1473108382
    assert identity.signature == "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw=="
    assert identity.member == False
    assert identity.membership_buid == BlockUID.empty()
    assert identity.membership_timestamp == 0
    assert identity.membership_written_on == 0
    identities_repo.drop(identity)
    identity = identities_repo.get_one(currency="testcurrency",
                                       pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                       uid="john",
                                       blockstamp=BlockUID(20,
                                                "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                                        )
    assert identity is None


def test_add_get_multiple_identity(meta_repo):
    identities_repo = IdentitiesRepo(meta_repo.conn)
    identities_repo.insert(Identity("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                    "john",
                                    "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                    "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                    1473108382))
    identities_repo.insert(Identity("testcurrency", "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                    "doe",
                                    "101-BAD49448A1AD73C978CEDCB8F137D20A5715EBAA739DAEF76B1E28EE67B2C00C",
                                    "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                    1455433535))
    identities = identities_repo.get_all(currency="testcurrency")
    assert "testcurrency" in [i.currency for i in identities]
    assert "john" in [i.uid for i in identities]
    assert "doe" in [i.uid for i in identities]


def test_add_update_identity(meta_repo):
    identities_repo = IdentitiesRepo(meta_repo.conn)
    identity = Identity("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                    "john",
                                    "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                    "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                    1473108382)
    identities_repo.insert(identity)
    identity.member = True
    identities_repo.update(identity)
    identity2 = identities_repo.get_one(currency="testcurrency",
                                        pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
    assert identity2.member is True
