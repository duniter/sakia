from duniterpy.documents import Peer
from sakia.data.connectors import NodeConnector


def test_from_peer():
    peer = Peer.from_signed_raw("""Version: 2
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API duniter.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
    connector = NodeConnector.from_peer('meta_brouzouf', peer, None)
    assert connector.node.pubkey == "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
    assert connector.node.endpoints[0].inline() == "BASIC_MERKLED_API duniter.inso.ovh 80"
    assert connector.node.currency == "meta_brouzouf"
