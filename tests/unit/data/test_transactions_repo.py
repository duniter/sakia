from sakia.data.repositories import TransactionsRepo
from sakia.data.entities import Transaction


def test_add_get_drop_transaction(meta_repo):
    transactions_repo = TransactionsRepo(meta_repo.conn)
    transactions_repo.insert(Transaction("testcurrency",
                                         "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                                         20,
                                         "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                         1473108382,
                                         "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                         "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                         "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                         1565,
                                         1,
                                         "",
                                         0,
                                         Transaction.TO_SEND))
    transaction = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
    assert transaction.currency == "testcurrency"
    assert transaction.sha_hash == "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365"
    assert transaction.written_block == 20
    assert transaction.blockstamp.number == 15
    assert transaction.blockstamp.sha_hash == "76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"
    assert transaction.timestamp == 1473108382
    assert transaction.signature == "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw=="
    assert transaction.amount == 1565
    assert transaction.amount_base == 1
    assert transaction.issuer == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert transaction.receiver == "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
    assert transaction.comment == ""
    assert transaction.txid == 0
    transactions_repo.drop(transaction)
    transaction = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
    assert transaction is None


def test_add_get_multiple_transaction(meta_repo):
    transactions_repo = TransactionsRepo(meta_repo.conn)
    transactions_repo.insert(Transaction("testcurrency",
                                         "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                                         12,
                                         "543-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                         1473108382,
                                         "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                         "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                         "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                         14,
                                         2,
                                         "Test",
                                         2,
                                         Transaction.TO_SEND))
    transactions_repo.insert(Transaction("testcurrency",
                                         "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                                         20,
                                         "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                         1473108382,
                                         "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                         "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                         "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                         1565,
                                         1,
                                         "",
                                         0,
                                         Transaction.TO_SEND))
    transactions = transactions_repo.get_all(currency="testcurrency")
    assert "testcurrency" in [t.currency for t in transactions]
    assert "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ" in [t.receiver for t in transactions]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in [t.issuer for t in transactions]


def test_add_update_transaction(meta_repo):
    transactions_repo = TransactionsRepo(meta_repo.conn)
    transaction = Transaction("testcurrency",
                              "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                              20,
                              "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                              1473108382,
                              "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                              "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                              "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                              1565,
                              1,
                              "",
                              0,
                              Transaction.TO_SEND)
    transactions_repo.insert(transaction)
    transaction.written_on = None
    transactions_repo.update(transaction)
    transaction2 = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
    assert transaction2.written_block == 20
