from sakia.data.repositories import NodesRepo
from sakia.data.entities import Node
from duniterpy.documents import BlockUID, BMAEndpoint, UnknownEndpoint, block_uid


def test_add_get_drop_node(meta_repo):
    nodes_repo = NodesRepo(meta_repo.conn)
    inserted = Node(currency="testcurrency",
                    pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                    endpoints="""BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                     peer_blockstamp=BlockUID.empty(),
                     uid="doe",
                     current_buid="15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                     current_ts=12376543345,
                     previous_buid="14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                     state=Node.ONLINE,
                     software="duniter",
                     version="0.30.17")
    nodes_repo.insert(inserted)
    node = nodes_repo.get_one(currency="testcurrency",
                              pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
    assert node.currency == "testcurrency"
    assert node.pubkey == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert node.endpoints[0] == BMAEndpoint("test-net.duniter.fr", "13.222.11.22", None, 9201)
    assert node.endpoints[1] == BMAEndpoint("testnet.duniter.org", None, None, 80)
    assert node.endpoints[2] == UnknownEndpoint("UNKNOWNAPI", ["some", "useless", "information"])
    assert node.previous_buid == block_uid("14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
    assert node.current_buid == block_uid("15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
    assert node.state == Node.ONLINE
    assert node.software == "duniter"
    assert node.version == "0.30.17"
    assert node.merkle_peers_root == Node.MERKLE_EMPTY_ROOT
    assert node.merkle_peers_leaves == tuple()

    nodes_repo.drop(node)
    node = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
    assert node is None


def test_add_get_multiple_node(meta_repo):
    nodes_repo = NodesRepo(meta_repo.conn)
    nodes_repo.insert(Node("testcurrency",
                           "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                           """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                           BlockUID.empty(),
                           "doe",
                           "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                           12376543345,
                           "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                           Node.ONLINE,
                           "duniter",
                           "0.30.17"))
    nodes_repo.insert(Node("testcurrency",
                           "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                           "BASIC_MERKLED_API test-net.duniter.org 22.22.22.22 9201",
                           BlockUID.empty(),
                           "doe",
                           "18-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                           12376543345,
                           "12-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                           Node.ONLINE,
                           "duniter",
                           "0.30.2a5"))
    nodes = nodes_repo.get_all(currency="testcurrency")
    assert "testcurrency" in  [t.currency for t in nodes]
    assert "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ" in  [n.pubkey for n in nodes]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in  [n.pubkey for n in nodes]


def test_add_update_node(meta_repo):
    nodes_repo = NodesRepo(meta_repo.conn)
    node = Node("testcurrency",
                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                BlockUID.empty(),
                "doe",
                "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                12376543345,
                "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                Node.ONLINE,
                "duniter")
    nodes_repo.insert(node)
    node.previous_buid = node.current_buid
    node.current_buid = "16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"
    nodes_repo.update(node)
    node2 = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
    assert node2.current_buid == block_uid("16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
    assert node2.previous_buid == block_uid("15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
