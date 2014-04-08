import pytest
import ucoinpy as ucoin
from mock import Mock, patch
from cutecoin.models.wallet import Wallet
from cutecoin.models.community import Community, CommunityNetwork

@pytest.fixture
def mock_community():
    def community_request(request):
        if type(request) is ucoin.hdc.coins.List:
            return {
            "owner": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
            "coins": [{
              "issuer": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
              "ids": ["1-5-2-A-1", "2-4-1-A-1"]
            },{
              "issuer": "31A6302161AC8F5938969E85399EB3415C237F93",
              "ids": ["10-1-2-F-14"]
            }]
            }
        else:
                assert 0
    mock_network=Mock(spec=CommunityNetwork, request=community_request)
    community = Mock(spec=Community, network=mock_network)
        
    return community


class Test_Wallet:
    def test_wallet_create(self, mock_community):
        wallet = Wallet([], mock_community)
        assert wallet is not None

        
    def test_wallet_load(self):
        pass


    def test_wallet_value(self, mock_community):
        wallet = Wallet([], mock_community)
        assert wallet.value() == 0
        wallet.refresh_coins("86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8")
        assert wallet.value() == 640
        pass


    def test_wallet_get_text(self):
        pass


    def test_wallet_jsonify(self):
        pass
