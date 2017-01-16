from sakia.data.entities import Identity
from duniterpy.documents.certification import Certification
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