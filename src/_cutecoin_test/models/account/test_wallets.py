import pytest
import ucoin
from mock import Mock, MagicMock
from cutecoin.models.wallet import Wallet
from cutecoin.models.account.wallets import Wallets
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

    mock_network = Mock(spec=CommunityNetwork, request=community_request)
    community = MagicMock(spec=Community, network=mock_network)

    return community


def mock_wallet():
    def wallet_eq(mock1, mock2):
        return mock1.community == mock2.community
    mock_wallet = MagicMock(spec=Wallet, __eq__=wallet_eq)


class Test_Wallets:
    def test_wallets_add_wallet(self):
        wallets = Wallets()
        wallet = wallets.add_wallet(mock_community())
        assert wallet is not None

    def test_wallets_get_wallet(self):
        mock1 = mock_community()
        mock2 = mock_community()
        mock3 = mock_community()
        mock_wallet1 = Mock(spec=Wallet, community=mock1)
        mock_wallet2 = Mock(spec=Wallet, community=mock2)
        mock_wallet3 = Mock(spec=Wallet, community=mock3)
        wallets = Wallets()
        wallets._wallets_list.append(mock_wallet1)
        wallets._wallets_list.append(mock_wallet2)

        assert wallets.get_wallet(mock_wallet1) is not None
        assert wallets.get_wallet(mock_wallet2) is not None
        assert wallets.get_wallet(mock_wallet3) is None

    def test_wallets_remove_all_wallets_of(self):
        mock1 = mock_community()
        mock2 = mock_community()
        mock_wallet1 = Mock(spec=Wallet, community=mock1)
        mock_wallet2 = Mock(spec=Wallet, community=mock2)
        wallets = Wallets()
        wallets._wallets_list.append(mock_wallet1)
        wallets._wallets_list.append(mock_wallet2)

        wallets.remove_all_wallets_of(mock1)
        assert wallets.get_wallet(mock_wallet1) is None
        assert wallets.get_wallet(mock_wallet2) is not None

