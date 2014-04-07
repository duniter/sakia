import pytest
import ucoinpy as ucoin
from mock import Mock
from cutecoin.models.wallet import Wallet
from cutecoin.models.community import Community

@pytest.fixture
def mock_coins_list_get():
	mock_get = Mock(spec=ucoin.hdc.coins.List.__get__)
	mock_get.return_value = {
	"owner": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
	"coins": [{
	  "issuer": "86F7E437FAA5A7FCE15D1DDCB9EAEAEA377667B8",
	  "ids": ["1-5-2-A-1", "2-4-1-A-1"]
	},{
	  "issuer": "31A6302161AC8F5938969E85399EB3415C237F93",
	  "ids": ["10-1-2-F-14"]
	}]
	}
	return mock_get


@pytest.fixture	
def mock_community_request(request, mock_coins_list_get):
		if request == ucoin.hdc.coins.List.get:
			return mock_coins_list_get()
		else:
			return "Failed !"


@pytest.fixture	
def mock_community(mock_community_request):
		community = Mock(spec=Community)
		instance = community.return_value
		instance.network.request.return_value = mock_community_request
		return community


class Test_Wallet:
	def test_wallet_create(self, mock_community):
		wallet = Wallet([], mock_community)
		assert wallet is not None

		
	def test_wallet_load(self):
		pass


	def test_wallet_value(self, mock_community):
		wallet = Wallet([], mock_community)
		assert wallet.value() == 640
		
		pass


	def test_wallet_refresh_coins(self):
		pass


	def test_wallet_get_text(self):
		pass


	def test_wallet_jsonify(self):
		pass
