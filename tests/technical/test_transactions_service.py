import pytest
from sakia.data.entities import Transaction


@pytest.mark.asyncio
async def test_send_tx_then_validate(application_with_one_connection, fake_server_with_blockchain, bob, alice):
    tx_before_send = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    bob_connection = application_with_one_connection.db.connections_repo.get_one(pubkey=bob.key.pubkey)
    await application_with_one_connection.documents_service.send_money(bob_connection,
                                                                       bob.salt,
                                                                       bob.password,
                                                                       alice.key.pubkey, 10, 0, "Test comment")
    tx_after_send = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    assert len(tx_before_send) + 1 == len(tx_after_send)
    assert tx_after_send[-1].state is Transaction.AWAITING
    assert tx_after_send[-1].written_block == 0
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    new_blocks = fake_server_with_blockchain.forge.blocks[-3:]
    await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    tx_after_parse = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    assert tx_after_parse[-1].state is Transaction.VALIDATED
    assert tx_after_parse[-1].written_block == fake_server_with_blockchain.forge.blocks[-3].number
    await fake_server_with_blockchain.close()


@pytest.mark.asyncio
async def test_receive_tx(application_with_one_connection, fake_server_with_blockchain, bob, alice):
    tx_before_send = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    fake_server_with_blockchain.forge.push(alice.send_money(10, fake_server_with_blockchain.forge.user_identities[alice.key.pubkey].sources, bob,
                                            fake_server_with_blockchain.forge.blocks[-1].blockUID, "Test receive"))
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    new_blocks = fake_server_with_blockchain.forge.blocks[-3:]
    await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    tx_after_parse = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    assert tx_after_parse[-1].state is Transaction.VALIDATED
    assert len(tx_before_send) + 1 == len(tx_after_parse)
    await fake_server_with_blockchain.close()


@pytest.mark.asyncio
async def test_issue_dividend(application_with_one_connection, fake_server_with_blockchain, bob):
    dividends_before_send = application_with_one_connection.transactions_service.dividends(bob.key.pubkey)
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.generate_dividend()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.generate_dividend()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.forge_block()
    new_blocks = fake_server_with_blockchain.forge.blocks[-5:]
    await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    dividends_after_parse = application_with_one_connection.transactions_service.dividends(bob.key.pubkey)
    assert len(dividends_before_send) + 2 == len(dividends_after_parse)
    await fake_server_with_blockchain.close()
