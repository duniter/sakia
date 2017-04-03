from sakia.data.entities import Identity
from duniterpy.documents.certification import Certification
import pytest


@pytest.mark.asyncio
async def test_new_block_with_ud(application_with_one_connection, fake_server_with_blockchain):
    previous_ud = application_with_one_connection.blockchain_service.previous_ud()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.generate_dividend()
    fake_server_with_blockchain.forge.forge_block()
    fake_server_with_blockchain.forge.generate_dividend()
    fake_server_with_blockchain.forge.forge_block()
    new_blocks = fake_server_with_blockchain.forge.blocks[-3:]
    application_with_one_connection.blockchain_service.handle_new_blocks(
        new_blocks)
    previous_ud_after_parse = application_with_one_connection.blockchain_service.previous_ud()
    assert previous_ud_after_parse > previous_ud
    await fake_server_with_blockchain.close()