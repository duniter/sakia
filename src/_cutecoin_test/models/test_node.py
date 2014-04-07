import pytest
import ucoinpy as ucoin
from mock import Mock
from cutecoin.models.node import Node

@pytest.fixture
def mock_peers_get():
	mock_get = Mock(spec=ucoin.ucg.peering.Peers.__get__)
	mock_get.return_value = [{
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
	}]
	return mock_get
	

@pytest.fixture
def mock_peer_get():
	mock_get = Mock(spec=ucoin.ucg.peering.Peer.__get__)
	mock_get.return_value = {
	"version": "1",
	"currency": "beta_brousouf",
	"fingerprint": "A70B8E8E16F91909B6A06DFB7EEF1651D9CCF468",
	"dns": "DNS_VALUE",
	"ipv4": "192.168.100.10",
	"ipv6": "",
	"port": "3800",
	"signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----"
	}
	return mock_get
	
class Test_Node():
	def test_peers(self, monkeypatch, mock_peers_get):

		monkeypatch.setattr(ucoin.ucg.peering.Peers, '__get__', mock_peers_get)

		node = Node("192.168.100.12", 3800)
		peers = node.peers()
		assert peers[0]["ipv4"] == "192.168.100.10"
		assert peers[1]["ipv4"] == "192.168.100.11"


	def test_peering(self, monkeypatch, mock_peer_get):
		monkeypatch.setattr(ucoin.ucg.peering.Peer, '__get__', mock_peer_get)

		node = Node("192.168.100.12", 3800)
		peering = node.peering()
		assert peering["ipv4"] == "192.168.100.10"
		assert peering["port"] == str(3800)


	def test_node_jsonify(self, monkeypatch):
		pass
