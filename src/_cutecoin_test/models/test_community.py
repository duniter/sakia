import pytest
from mock import Mock
import ucoin
from cutecoin.models.community import Community
from cutecoin.models.community import Node
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.account import Account
from cutecoin.models.node import Node



amendment_hash =  "3682F828EFB1A1AFF45ACC6DDBB2BAD100DCD605"

def patch_amendment_Promoted_get(*args, **kwargs):
    return {
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
    "raw": """Version: 1
Currency: beta_brousouf
Number: 2
Dividend: 100
CoinMinimalPower: 0
PreviousHash: 0F45DFDA214005250D4D2CBE4C7B91E60227B0E5
MembersRoot: F92B6F81C85200250EE51783F5F9F6ACA57A9AFF
MembersCount: 4
MembersChanges:
+31A6302161AC8F5938969E85399EB3415C237F93
VotersRoot: DC7A9229DFDABFB9769789B7BFAE08048BCB856F
VotersCount: 2
VotersChanges:
-C73882B64B7E72237A2F460CE9CAB76D19A8651E
"""
    }


def patch_amendments_members_get(*args, **kwargs):
    return iter([{
    "hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
    "value": "2E69197FAB029D8669EF85E82457A1587CA0ED9C"
    },
    {
    "hash": "3F870197FAB029D8669EF85E82457A1587CA0ED9C",
    "value": "3F870197FAB029D8669EF85E82457A1587CA0ED9C"
    },
    {
    "hash": "3F69197FAB029D8669EF85E82457A1587CA0ED9C",
    "value": "3F69197FAB029D8669EF85E82457A1587CA0ED9C"
    }])


def patch_amendments_voters_get(*args, **kwargs):
    return iter([{
    "hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
    "value": "2E69197FAB029D8669EF85E82457A1587CA0ED9C"
    },
    {
    "hash": "3F870197FAB029D8669EF85E82457A1587CA0ED9C",
    "value": "3F870197FAB029D8669EF85E82457A1587CA0ED9C"
    }])


@pytest.fixture
def mock_node():
    def node_use(request):
        return request

    mock = Mock(spec=Node, trust=True, hoster=True,
                server="192.168.100.10", port=3800)
    mock.get_text.return_value = "Mock node"
    mock.use = node_use
    return mock


class Test_Community():
    def test_community_create(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        community = Community.create(mock_node)
        assert community is not None

    def test_community_dividend(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        community = Community.create(mock_node)
        assert community.dividend() == 100

    def test_community_coin_minimal_power(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        community = Community.create(mock_node)
        assert community.coin_minimal_power() == 0

    def test_community_amendment_id(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        community = Community.create(mock_node)
        assert community.amendment_id() == "2-"+amendment_hash.upper()

    def test_community_amendment_number(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        community = Community.create(mock_node)
        assert community.amendment_number() == 2

    def test_community_person_quality(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        monkeypatch.setattr(ucoin.registry.community.Members,
                            '__get__', patch_amendments_members_get)
        monkeypatch.setattr(ucoin.registry.community.Voters,
                            '__get__', patch_amendments_voters_get)
        community = Community.create(mock_node)
        assert community.person_quality("2E69197FAB029D8669EF85E82457A1587CA0ED9C") == "voter"
        assert community.person_quality("3F69197FAB029D8669EF85E82457A1587CA0ED9C") == "member"
        assert community.person_quality("3F870197FAB029D8669EF85E82457A1587CA0ED9C") == "voter"
        assert community.person_quality("3F871197FAB029D8669EF85E82457A1587CA0ED9C") == "nothing"

    def test_community_members_fingerprint(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        monkeypatch.setattr(ucoin.registry.community.Members,
                            '__get__', patch_amendments_members_get)
        monkeypatch.setattr(ucoin.registry.community.Voters,
                            '__get__', patch_amendments_voters_get)
        community = Community.create(mock_node)

        assert "2E69197FAB029D8669EF85E82457A1587CA0ED9C" in community.members_fingerprints()
        assert "3F69197FAB029D8669EF85E82457A1587CA0ED9C" in community.members_fingerprints()
        assert "3F870197FAB029D8669EF85E82457A1587CA0ED9C" in community.members_fingerprints()
        assert "3F871197FAB029D8669EF85E82457A1587CA0ED9C"  not in community.members_fingerprints()

    def test_community_voters_fingerprint(self, monkeypatch, mock_node):
        monkeypatch.setattr(ucoin.registry.community.Members,
                            '__get__', patch_amendment_Promoted_get)
        monkeypatch.setattr(ucoin.registry.community.Members,
                            '__get__', patch_amendments_members_get)
        monkeypatch.setattr(ucoin.registry.community.Voters,
                            '__get__', patch_amendments_voters_get)
        community = Community.create(mock_node)

        assert "2E69197FAB029D8669EF85E82457A1587CA0ED9C" in community.voters_fingerprints()
        assert "3F870197FAB029D8669EF85E82457A1587CA0ED9C" in community.voters_fingerprints()
        assert "3F871197FAB029D8669EF85E82457A1587CA0ED9C" not in community.voters_fingerprints()

    def test_community_jsonify(self, monkeypatch):
        monkeypatch.setattr(ucoin.hdc.amendments.Promoted,
                            '__get__', patch_amendment_Promoted_get)
        main_node = Node.create(trust=True, hoster=True,
                server="192.168.100.10", port=3800)
        community = Community.create(main_node)
        wallets = Wallets()
        json = community.jsonify(wallets)
        account = Mock(spec=Account)
        community2 = Community.load(json, account)

        assert community2.network.nodes[0].server == community.network.nodes[0].server
