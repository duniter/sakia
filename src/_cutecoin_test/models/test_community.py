import pytest
from mock import Mock
import ucoinpy as ucoin
from cutecoin.models.community import Community
from cutecoin.models.community import Node


@pytest.fixture
def mock_amendment_current_get():
	mock_get = Mock(spec=ucoin.hdc.amendments.Current.__get__)
	mock_get.return_value = {
	"version": "1",
	"currency": "beta_brousouf",
	"number": "2",
	"previousHash": "0F45DFDA214005250D4D2CBE4C7B91E60227B0E5",
	"dividend": "100",
	"coinMinimalPower": "0",
	"votersRoot": "DC7A9229DFDABFB9769789B7BFAE08048BCB856F",
	"votersCount": "2",
	"votersChanges": [
	"-C73882B64B7E72237A2F460CE9CAB76D19A8651E"
	],
	"membersRoot": "F92B6F81C85200250EE51783F5F9F6ACA57A9AFF",
	"membersCount": "4",
	"membersChanges": [
	"+31A6302161AC8F5938969E85399EB3415C237F93"
	],
	"raw": "Version: 1\r\n...+31A6302161AC8F5938969E85399EB3415C237F93\r\n"
	}
	return mock_get


@pytest.fixture
def mock_amendments_members_get():
	mock_get = Mock(spec=ucoin.hdc.amendments.Current.__get__)
	mock_get.return_value = [{
	"hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
	"value": "2E69197FAB029D8669EF85E82457A1587CA0ED9C"
	},
	{
	"hash": "3F69197FAB029D8669EF85E82457A1587CA0ED9C",
	"value": "3F69197FAB029D8669EF85E82457A1587CA0ED9C"
	}]
	return mock_get

	
@pytest.fixture
def mock_amendments_voters_get():
	mock_get = Mock(spec=ucoin.hdc.amendments.Current.__get__)
	mock_get.return_value = [{
	"hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
	"value": "2E69197FAB029D8669EF85E82457A1587CA0ED9C"
	},
	{
	"hash": "3F69197FAB029D8669EF85E82457A1587CA0ED9C",
	"value": "3F69197FAB029D8669EF85E82457A1587CA0ED9C"
	}]
	return mock_get
	
	

class Test_Community():
	def test_community_create(self, monkeypatch, mock_amendment_current_get):
			pass


	def test_community_dividend(self, monkeypatch):
		pass


	def test_community_coin_minimal_power(self, monkeypatch):
		pass


	def test_community_amendment_id(self, monkeypatch):
		pass


	def test_community_amendment_number(self, monkeypatch):
		pass


	def test_community_person_quality(self, monkeypatch):
		pass


	def test_community_members_fingerprint(self, monkeypatch):
		pass


	def test_community_voters_fingerprint(self, monkeypatch):
		pass


	def test_community_to_json(self):
		pass


	def test_community_from_json(self):
		pass
