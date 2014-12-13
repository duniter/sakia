'''
Created on 13 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.peer import Peer, BMAEndpoint, UnknownEndpoint


rawpeer = """Version: 1
Type: Peer
Currency: beta_brousouf
PublicKey: HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY
Block: 8-1922C324ABC4AF7EF7656734A31F5197888DDD52
Endpoints:
BASIC_MERKLED_API some.dns.name 88.77.66.55 2001:0db8:0000:85a3:0000:0000:ac1f 9001
BASIC_MERKLED_API some.dns.name 88.77.66.55 2001:0db8:0000:85a3:0000:0000:ac1f 9002
OTHER_PROTOCOL 88.77.66.55 9001
dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==
"""


class TestPeer:
    def test_fromraw(self):
        peer = Peer.from_signed_raw(rawpeer)
        assert peer.currency == "beta_brousouf"
        assert peer.pubkey == "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY"
        assert peer.blockid == "8-1922C324ABC4AF7EF7656734A31F5197888DDD52"
        assert len(peer.endpoints) == 3
        assert type(peer.endpoints[0]) is BMAEndpoint
        assert type(peer.endpoints[1]) is BMAEndpoint
        assert type(peer.endpoints[2]) is UnknownEndpoint

        assert peer.endpoints[0].server == "some.dns.name"
        assert peer.endpoints[0].ipv4 == "88.77.66.55"
        assert peer.endpoints[0].ipv6 == "2001:0db8:0000:85a3:0000:0000:ac1f"
        assert peer.endpoints[0].port == 9001

        assert peer.endpoints[1].server == "some.dns.name"
        assert peer.endpoints[1].ipv4 == "88.77.66.55"
        assert peer.endpoints[1].ipv6 == "2001:0db8:0000:85a3:0000:0000:ac1f"
        assert peer.endpoints[1].port == 9002

        assert peer.signatures[0] == "dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg=="

    def test_fromraw_toraw(self):
        peer = Peer.from_signed_raw(rawpeer)
        rendered_peer = peer.signed_raw()
        from_rendered_peer = Peer.from_signed_raw(rendered_peer)

        assert from_rendered_peer.currency == "beta_brousouf"
        assert from_rendered_peer.pubkey == "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY"
        assert from_rendered_peer.blockid == "8-1922C324ABC4AF7EF7656734A31F5197888DDD52"
        assert len(from_rendered_peer.endpoints) == 3
        assert type(from_rendered_peer.endpoints[0]) is BMAEndpoint
        assert type(from_rendered_peer.endpoints[1]) is BMAEndpoint
        assert type(from_rendered_peer.endpoints[2]) is UnknownEndpoint

        assert from_rendered_peer.endpoints[0].server == "some.dns.name"
        assert from_rendered_peer.endpoints[0].ipv4 == "88.77.66.55"
        assert from_rendered_peer.endpoints[0].ipv6 == "2001:0db8:0000:85a3:0000:0000:ac1f"
        assert from_rendered_peer.endpoints[0].port == 9001

        assert from_rendered_peer.endpoints[1].server == "some.dns.name"
        assert from_rendered_peer.endpoints[1].ipv4 == "88.77.66.55"
        assert from_rendered_peer.endpoints[1].ipv6 == "2001:0db8:0000:85a3:0000:0000:ac1f"
        assert from_rendered_peer.endpoints[1].port == 9002

        assert from_rendered_peer.signatures[0] == "dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg=="


