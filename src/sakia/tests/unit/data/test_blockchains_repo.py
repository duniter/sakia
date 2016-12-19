from duniterpy.documents import BlockUID

from sakia.data.entities import Blockchain, BlockchainParameters
from sakia.data.repositories import BlockchainsRepo


def test_add_get_drop_blockchain(meta_repo):
    blockchains_repo = BlockchainsRepo(meta_repo.conn)
    blockchains_repo.insert(Blockchain(
        parameters=BlockchainParameters(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66),
        current_buid="20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
        current_members_count = 10,
        current_mass = 1000000,
        median_time = 86400,
        last_members_count = 5,
        last_ud = 100000,
        last_ud_base = 0,
        last_ud_time = 86400,
        previous_mass = 999999,
        previous_members_count = 10,
        previous_ud = 6543,
        previous_ud_base = 0,
        previous_ud_time = 86400,
        currency = "testcurrency"
    ))
    blockchain = blockchains_repo.get_one(currency="testcurrency")
    assert blockchain.parameters == BlockchainParameters(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66)
    assert blockchain.currency == "testcurrency"
    assert blockchain.current_buid == BlockUID(20, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
    assert blockchain.current_members_count == 10

    blockchains_repo.drop(blockchain)
    blockchain = blockchains_repo.get_one(currency="testcurrency")
    assert blockchain is None

def test_add_get_multiple_blockchain(meta_repo):
    blockchains_repo = BlockchainsRepo(meta_repo.conn)
    blockchains_repo.insert(Blockchain(
        parameters=BlockchainParameters(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66),

        current_buid="20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
        current_members_count = 10,
        current_mass = 1000000,
        median_time = 86400,
        last_members_count = 5,
        last_ud = 100000,
        last_ud_base = 0,
        last_ud_time = 86400,
        previous_mass = 999999,
        previous_members_count = 10,
        previous_ud = 6543,
        previous_ud_base = 0,
        previous_ud_time = 86400,
        currency = "testcurrency"
    ))
    blockchains_repo.insert(Blockchain(
        BlockchainParameters(
            0.1,
            86400 * 365,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66),
        current_buid="20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
        current_members_count = 20,
        current_mass = 1000000,
        median_time = 86400,
        last_members_count = 5,
        last_ud = 100000,
        last_ud_base = 0,
        last_ud_time = 86400,
        previous_mass = 999999,
        previous_members_count = 10,
        previous_ud = 6543,
        previous_ud_base = 0,
        previous_ud_time = 86400,
        currency = "testcurrency2"
    ))

    blockchains = blockchains_repo.get_all()
    # result sorted by currency name by default
    assert 86400 == blockchains[0].parameters.dt
    assert "testcurrency" == blockchains[0].currency
    assert 10 == blockchains[0].current_members_count

    assert 86400*365 == blockchains[1].parameters.dt
    assert "testcurrency2" == blockchains[1].currency
    assert 20 == blockchains[1].current_members_count

def test_add_update_blockchain(meta_repo):
    blockchains_repo = BlockchainsRepo(meta_repo.conn)
    blockchain = Blockchain(
        BlockchainParameters(
            0.1,
            86400,
            100000,
            10800,
            40,
            2629800,
            31557600,
            1,
            0.9,
            604800,
            5,
            12,
            300,
            25,
            10,
            0.66),
        current_buid="20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
        current_members_count = 10,
        current_mass = 1000000,
        median_time = 86400,
        last_members_count = 5,
        last_ud = 100000,
        last_ud_base = 0,
        last_ud_time = 86400,
        previous_mass = 999999,
        previous_members_count = 10,
        previous_ud = 6543,
        previous_ud_base = 0,
        previous_ud_time = 86400,
        currency = "testcurrency"
    )
    blockchains_repo.insert(blockchain)
    blockchain.current_members_count = 30
    blockchains_repo.update(blockchain)
    blockchain2 = blockchains_repo.get_one(currency="testcurrency")
    assert 30 == blockchain2.current_members_count
