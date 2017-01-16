from sakia.data.entities import Identity
from duniterpy.documents.certification import Certification
import pytest


@pytest.mark.asyncio
async def test_new_block_with_ud(application_with_one_connection, fake_server):
    previous_ud = application_with_one_connection.blockchain_service.previous_ud()
    fake_server.forge.forge_block()
    fake_server.forge.generate_dividend()
    fake_server.forge.forge_block()
    fake_server.forge.generate_dividend()
    fake_server.forge.forge_block()
    new_blocks = fake_server.forge.blocks[-3:]
    application_with_one_connection.blockchain_service.handle_new_blocks(
        new_blocks)
    previous_ud_after_parse = application_with_one_connection.blockchain_service.previous_ud()
    assert previous_ud_after_parse > previous_ud
    await fake_server.close()