import pytest
from sakia.data.processors import ConnectionsProcessor


@pytest.mark.asyncio
async def test_send_more_than_40_sources(application_with_one_connection, fake_server_with_blockchain, bob, alice):
    for i in range(0, 60):
        fake_server_with_blockchain.forge.generate_dividend()
        fake_server_with_blockchain.forge.forge_block()

    new_blocks = fake_server_with_blockchain.forge.blocks[-60:]
    connections = ConnectionsProcessor.instanciate(application_with_one_connection).connections()
    changed_tx, new_tx, new_ud = await application_with_one_connection.transactions_service.handle_new_blocks(connections,
                                                                                                              new_blocks)

    for conn in new_tx:
        await application_with_one_connection.sources_service.refresh_sources_of_pubkey(bob.key.pubkey, new_tx[conn], new_ud[conn], None)
    amount_before_send = application_with_one_connection.sources_service.amount(bob.key.pubkey)
    bob_connection = application_with_one_connection.db.connections_repo.get_one(pubkey=bob.key.pubkey)

    result, transactions = await application_with_one_connection.documents_service.send_money(bob_connection,
                                                                       bob.salt,
                                                                       bob.password,
                                                                       alice.key.pubkey,
                                                                       amount_before_send,
                                                                       0,
                                                                       "Test comment")
    assert transactions[0].comment == "[CHAINED]"
    assert transactions[1].comment == "Test comment"
    amount_after_send = application_with_one_connection.sources_service.amount(bob.key.pubkey)
    assert amount_after_send == 0

    await fake_server_with_blockchain.close()
