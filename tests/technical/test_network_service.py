import pytest
import os
from duniterpy.documents import block_uid
from sakia.data.entities import Node
from sakia.data.processors import NodesProcessor


@pytest.mark.asyncio
async def test_bug_614(application_with_one_connection, fake_server, bob, alice):
    sql_file = open(os.path.join(os.path.dirname(__file__), 'bug614.sql'), 'r')
    with application_with_one_connection.db.conn:
        application_with_one_connection.db.conn.executescript(sql_file.read())
    application_with_one_connection.network_service.check_nodes_sync(None)
    nodes = NodesProcessor.instanciate(application_with_one_connection).nodes("test_currency")
    for n in [node for node in nodes
              if node.current_buid == block_uid("9325-000031D0C7F53E4D8E35CAD22A11EAA99232F7FC79A2C12F25BF46330136FDB8")]:
        assert n.state == Node.ONLINE

    await fake_server.close()
