from sakia.data.entities import Identity, Connection
from duniterpy.documents import Certification, BlockUID

import pytest


@pytest.mark.asyncio
async def test_new_block_with_certs(application_with_one_connection, fake_server, bob, alice):
    certs_before_send = application_with_one_connection.identities_service.certifications_sent(
        bob.key.pubkey)
    alice_user_identity = fake_server.forge.user_identities[bob.key.pubkey]
    alice_identity = Identity(currency=fake_server.forge.currency,
                            pubkey=alice.key.pubkey,
                            uid=alice.uid,
                            blockstamp=alice_user_identity.blockstamp,
                            signature=alice_user_identity.signature)
    bob_connection = application_with_one_connection.db.connections_repo.get_one(pubkey=bob.key.pubkey)
    await application_with_one_connection.documents_service.certify(bob_connection,
                                                                       bob.password, alice_identity)
    certs_after_send = application_with_one_connection.identities_service.certifications_sent(
        bob.key.pubkey)
    assert len(certs_after_send) == len(certs_before_send) + 1
    assert certs_after_send[0].written_on == 0
    assert isinstance(fake_server.forge.pool[0], Certification)
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    new_blocks = fake_server.forge.blocks[-3:]
    await application_with_one_connection.identities_service.handle_new_blocks(
        new_blocks)
    certs_after_parse = application_with_one_connection.identities_service.certifications_sent(
        bob.key.pubkey)
    assert len(certs_after_parse) == len(certs_after_send)
    assert certs_after_parse[0].written_on == fake_server.forge.blocks[-3].number
    await fake_server.close()


@pytest.mark.asyncio
async def test_new_block_with_idty(application_with_one_connection, john, simple_fake_server):
    john_identity = Identity(currency=simple_fake_server.forge.currency,
                            pubkey=john.key.pubkey,
                            uid=john.uid,
                            blockstamp=john.blockstamp,
                            signature=john.identity().signatures[0])
    john_connection = Connection(currency="test_currency",
                      pubkey=john.key.pubkey,
                      salt=john.salt, uid=john.uid,
                      scrypt_N=4096, scrypt_r=4, scrypt_p=2,
                      blockstamp=john.blockstamp)
    application_with_one_connection.db.connections_repo.insert(john_connection)
    application_with_one_connection.db.identities_repo.insert(john_identity)
    application_with_one_connection.instanciate_services()

    john_found = application_with_one_connection.db.identities_repo.get_one(pubkey=john_identity.pubkey)
    assert john_found.written is False
    simple_fake_server.forge.forge_block()
    simple_fake_server.forge.push(john.identity())
    simple_fake_server.forge.push(john.join(BlockUID.empty()))
    simple_fake_server.forge.forge_block()
    simple_fake_server.forge.forge_block()
    new_blocks = simple_fake_server.forge.blocks[-3:]
    await application_with_one_connection.identities_service.handle_new_blocks(
        new_blocks)
    john_found = application_with_one_connection.db.identities_repo.get_one(pubkey=john_identity.pubkey)
    assert john_found.written is True
    await simple_fake_server.close()
