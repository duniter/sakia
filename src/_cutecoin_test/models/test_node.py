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
    
def patch_downstream_get(*args, **kwargs):
    return {
      "peers": [
        {"key": "SOME_KEY_FINGERPRINT", "dns": "name.example1.com", "ipv4": "11.11.11.11", "ipv6": "1A01:E35:2421:4BE0:CDBC:C04E:A7AB:ECF1", "port": 8881},
        {"key": "SOME_KEY_FINGERPRINT", "dns": "name.example2.com", "ipv4": "11.11.11.12", "ipv6": "1A01:E35:2421:4BE0:CDBC:C04E:A7AB:ECF2", "port": 8882}
      ]
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

    def test_eq(self, monkeypatch):
        node1 = Node("192.168.100.12", 3800)
        node2 = Node("192.168.100.13", 3800)
        node3 = Node("192.168.100.12", 3801)
        node4 = Node("192.168.100.12", 3800)

        assert node1 != node2
        assert node1 != node3
        assert node1 == node4
        
    def test_downstream(self, monkeypatch):
        monkeypatch.setattr(ucoin.ucg.peering.peers.DownStream, '__get__', patch_downstream_get)
        node = Node("192.168.100.12", 3800)
        downstream = node.downstream_peers()
        assert downstream[0].server == "11.11.11.11" and downstream[0].port == 8881
        assert downstream[1].server == "11.11.11.12" and downstream[1].port == 8882
    