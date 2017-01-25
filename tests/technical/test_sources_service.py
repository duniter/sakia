import pytest
from sakia.data.entities import Transaction


@pytest.mark.asyncio
async def test_receive_source(application_with_one_connection, fake_server, bob, alice):
    amount = application_with_one_connection.sources_service.amount(bob.key.pubkey)
    fake_server.forge.push(alice.send_money(150, fake_server.forge.user_identities[alice.key.pubkey].sources, bob,
                                            fake_server.forge.blocks[-1].blockUID, "Test receive"))
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    new_blocks = fake_server.forge.blocks[-3:]
    changed_tx, new_tx, new_ud = await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    await application_with_one_connection.sources_service.refresh_sources(new_tx, new_ud)
    assert amount + 150 == application_with_one_connection.sources_service.amount(bob.key.pubkey)
    await fake_server.close()


@pytest.mark.asyncio
async def test_send_source(application_with_one_connection, fake_server, bob, alice):
    amount = application_with_one_connection.sources_service.amount(bob.key.pubkey)
    fake_server.forge.push(bob.send_money(150, fake_server.forge.user_identities[bob.key.pubkey].sources, alice,
                                            fake_server.forge.blocks[-1].blockUID, "Test receive"))
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    new_blocks = fake_server.forge.blocks[-3:]
    changed_tx, new_tx, new_ud = await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    await application_with_one_connection.sources_service.refresh_sources(new_tx, new_ud)
    assert amount - 150 == application_with_one_connection.sources_service.amount(bob.key.pubkey)
    await fake_server.close()



@pytest.mark.asyncio
async def test_destruction(application_with_one_connection, fake_server, bob, alice):
    amount = application_with_one_connection.sources_service.amount(bob.key.pubkey)
    fake_server.forge.push(bob.send_money(amount - 80, fake_server.forge.user_identities[bob.key.pubkey].sources, alice,
                                            fake_server.forge.blocks[-1].blockUID, "Test receive"))
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    new_blocks = fake_server.forge.blocks[-3:]
    changed_tx, new_tx, new_ud = await application_with_one_connection.transactions_service.handle_new_blocks(new_blocks)
    await application_with_one_connection.sources_service.refresh_sources(new_tx, new_ud)
    assert 0 == application_with_one_connection.sources_service.amount(bob.key.pubkey)
    tx_after_parse = application_with_one_connection.transactions_service.transfers(bob.key.pubkey)
    assert tx_after_parse[-1].comment == "Too low balance"
    await fake_server.close()

