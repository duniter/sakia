import pytest
import ucoinpy as ucoin
from mock import Mock
from cutecoin.models.node import Node


def patch_peers_get(*args, **kwargs):
    return iter([{
    "version": "1",
    "currency": "beta_brousouf",
    "fingerprint": "A70B8E8E16F91909B6A06DFB7EEF1651D9CCF468",
    "dns": "DNS_VALUE",
    "ipv4": "192.168.100.10",
    "ipv6": "",
    "port": "3800",
    "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----"
    },
    {
    "version": "1",
    "currency": "beta_brousouf",
    "fingerprint": "A70B8E8E16F91909B6A06DFB7EEF1651D9CCF469",
    "dns": "DNS_VALUE",
    "ipv4": "192.168.100.11",
    "ipv6": "",
    "port": "3801",
    "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----"
    }])


def patch_peer_get(*args, **kwargs):
    return {
    "version": "1",
    "currency": "beta_brousouf",
    "fingerprint": "A70B8E8E16F91909B6A06DFB7EEF1651D9CCF468",
    "dns": "DNS_VALUE",
    "ipv4": "192.168.100.10",
    "ipv6": "",
    "port": "3800",
    "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----"
    }


class Test_Node():
    def test_peers(self, monkeypatch):

        monkeypatch.setattr(ucoin.ucg.peering.Peers,
                              '__get__', patch_peers_get)
        node = Node("192.168.100.12", 3800)
        assert (peer for peer in node.peers() if peer["ipv4"] == "192.168.100.10")
        assert (peer for peer in node.peers() if peer["ipv4"] == "192.168.100.11")

    def test_peering(self, monkeypatch):
        monkeypatch.setattr(ucoin.ucg.peering.Peer, '__get__', patch_peer_get)

        node = Node("192.168.100.12", 3800)
        peering = node.peering()
        assert peering["ipv4"] == "192.168.100.10"
        assert peering["port"] == str(3800)

    #TODO: Test node json
    def test_node_jsonify(self, monkeypatch):
        pass
