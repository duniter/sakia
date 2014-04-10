import pytest
import ucoinpy as ucoin
from mock import Mock, MagicMock, patch
from cutecoin.models.wallet import Wallet
from cutecoin.models.community import Community, CommunityNetwork


def mock_community():
    def community_request(request):
        if type(request) is ucoin.hdc.coins.List:
            return {
            "owner": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
            "coins": [{
              "issuer": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
              "ids": ["1-5-2-A-1", "2-4-1-A-1"]
            },
            {
              "issuer": "31A6302161AC8F5938969E85399EB3415C237F93",
              "ids": ["10-1-2-F-14"]
            }]
            }
        else:
                assert 0
            
    def community_eq(mock1, mock2):
            return mock1.amendment_id() == mock2.amendment_id()
                
    mock_network = Mock(spec=CommunityNetwork, request=community_request)
    community = MagicMock(spec=Community, network=mock_network, __eq__=community_eq)

    return community


class Test_Wallet:
    def test_wallet_create(self,):
        wallet = Wallet([], mock_community())
        assert wallet is not None

    #TODO: Test json
    def test_wallet_load(self):
        pass

    def test_wallet_value(self):
        wallet = Wallet([], mock_community())
        assert wallet.value() == 0
        wallet.refresh_coins("86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8")
        assert wallet.value() == 640
        pass

    def test_wallet_get_text(self):
        pass
        
    def test_eq(self):
        mock1 = mock_community()
        mock1.amendment_id.return_value = "2-AMENDMENTTEST"
        mock2 = mock_community()
        mock2.amendment_id.return_value =  "2-AMENDMENTTEST"
        wallet1 = Wallet([], mock1)
        wallet2 = Wallet([], mock2)

        assert wallet1 == wallet2
        
    def test_not_eq(self):
        mock1 = mock_community()
        mock1.amendment_id.return_value = "2-AMENDMENTTEST"
        mock2 = mock_community()
        mock2.amendment_id.return_value =  "1-AMENDMENTTEST"
        wallet1 = Wallet([], mock1)
        wallet2 = Wallet([], mock2)

        assert wallet1 != wallet2
        
    def test_wallet_jsonify(self, monkeypatch):
        wallet = Wallet([], mock_community())
        wallet.refresh_coins("86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8")
        json = wallet.jsonify()
        wallet2 = Wallet.load(json, mock_community())
        same_coins = [coin1 for coin1, coin2 in zip(wallet.coins, wallet2.coins) if coin1 == coin2]
        assert len(same_coins) == len(wallet.coins) and len(same_coins) == len(wallet2.coins) 