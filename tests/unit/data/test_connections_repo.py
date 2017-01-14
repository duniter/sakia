from sakia.data.repositories import ConnectionsRepo
from sakia.data.entities import Connection

def test_add_get_drop_connection(meta_repo):
    connections_repo = ConnectionsRepo(meta_repo.conn)
    connections_repo.insert(Connection("testcurrency",
                                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                             "somesalt"))
    connection = connections_repo.get_one(currency="testcurrency",
                                       pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                       salt="somesalt")
    assert connection.currency == "testcurrency"
    assert connection.pubkey == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert connection.salt == "somesalt"
    connections_repo.drop(connection)
    connection = connections_repo.get_one(currency="testcurrency",
                                       pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                       salt="somesalt")
    assert connection is None
