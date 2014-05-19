import pytest
import ucoin
import gnupg
from mock import Mock
from cutecoin.models.account import Account
from cutecoin.models.account.communities import Communities
from cutecoin.models.community import Community, CommunityNetwork


user_keys = {
    "0x31A6302161AC8F5938969E85399EB3415C237F93" : {
     "keys": [
        {
          "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
          "key":
          {
            "email":"mistertest@testmail.com",
            "comment":"",
            "name":"Mister test",
            "fingerprint":"31A6302161AC8F5938969E85399EB3415C237F93",
            "raw":"-----BEGIN PGP PUBLIC KEY BLOCK----- ... -----END PGP PUBLIC KEY BLOCK-----\r\n"
          }
        }
     ]
     },
    "0x2E69197FAB029D8669EF85E82457A1587CA0ED9C" : {
    "keys": [
        {
          "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
          "key":
          {
            "email":"mistertest2@testmail.com",
            "comment":"",
            "name":"Mister test2",
            "fingerprint":"2E69197FAB029D8669EF85E82457A1587CA0ED9C",
            "raw":"-----BEGIN PGP PUBLIC KEY BLOCK----- ... -----END PGP PUBLIC KEY BLOCK-----\r\n"
          }
        }
    ]
    }
}

def patch_transactions_recipient_get(*arg, **kwargs):
    return iter([{
      "hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
      "value": {
        "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
        "transaction":
        {
        "version": 1,
        "currency": "beta_brousouf",
        "sender": "31A6302161AC8F5938969E85399EB3415C237F93",
        "number": 15,
        "previousHash": "BE522363749E62BA1034C7B1358B01C75289DA48",
        "recipient": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
        "type": "TRANSFER",
        "coins": [
          {
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-10-1-2-F-14",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-2-4-1-A-1",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-3-6-1-A-1",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          }
        ],
        "comment": "Too much coins ! Making big one."
        }
      }
    }])


def patch_transactions_sent_get(*arg, **kwargs):
    return iter([{
      "hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
      "value": {
        "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
        "transaction":
        {
        "version": 1,
        "currency": "beta_brousouf",
        "sender": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
        "number": 15,
        "previousHash": "BE522363749E62BA1034C7B1358B01C75289DA48",
        "recipient": "31A6302161AC8F5938969E85399EB3415C237F93",
        "type": "TRANSFER",
        "coins": [
          {
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-10-1-2-F-14",
            "transaction_id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-2-4-1-A-1",
            "transaction_id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-3-6-1-A-1",
            "transaction_id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-1"
          }
        ],
        "comment": "Too much coins ! Making big one."
        }
      }
    }])


def patch_transactions_view_get(*arg, **kwargs):
    return {
        "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
         "transaction":
        {
        "version": 1,
        "currency": "beta_brousouf",
        "sender": "31A6302161AC8F5938969E85399EB3415C237F93",
        "number": 15,
        "previousHash": "BE522363749E62BA1034C7B1358B01C75289DA48",
        "recipient": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
        "type": "TRANSFER",
        "coins": [
          {
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-10-1-2-F-14",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-2-4-1-A-1",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          },{
            "id": "31A6302161AC8F5938969E85399EB3415C237F93-3-6-1-A-1",
            "transaction_id": "31A6302161AC8F5938969E85399EB3415C237F93-1"
          }
        ],
        "comment": "Too much coins ! Making big one."
        }
    }

def patch_transactions_issuances_get(*arg, **kwargs):
    return iter([{
      "hash": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
      "value": {
        "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
         "transaction":
            {
            "version": 1,
            "currency": "beta_brousouf",
            "sender": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
            "number": 1,
            "previousHash": "BE522363749E62BA1034C7B1358B01C75289DA48",
            "recipient": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
            "type": "ISSUANCE",
            "coins": [
            {
                "id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-2-4-1-A-1",
                "transaction_id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-1"
              },{
                "id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-3-6-1-A-1",
                "transaction_id": "2E69197FAB029D8669EF85E82457A1587CA0ED9C-1"
              }
            ],
            "comment": "Too much coins ! Making big one."
            }
        }
    }
    ])

def mock_gpg():
    def gpg_list_keys():
        return [{
        'keyid': u'25500A07',
        'fingerprint': '2E69197FAB029D8669EF85E82457A1587CA0ED9C',
        'uids': [u'Mister Test <mister_test@testmail.com>'],
        'expires': u'',
        'length': u'1024',
        'algo': u'17',
        'date': u'1221156445',
        'type': u'pub'
        }]

    mock = Mock(spec=gnupg.GPG)
    instance = mock.return_value
    instance.list_keys = gpg_list_keys
    return instance


@pytest.fixture
def mock_community():
    def community_request(request, get_args={}):
        if type(request) is ucoin.hdc.transactions.Recipient:
            return patch_transactions_recipient_get()
        elif type(request) is ucoin.hdc.transactions.sender.Last:
            return patch_transactions_sent_get()
        elif type(request) is ucoin.hdc.coins.List:
            return {
            "owner": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
            "coins": [{
              "issuer": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
              "ids": ["1-5-2-A-1", "2-4-1-A-1"]
            },
            {
              "issuer": "2E69197FAB029D8669EF85E82457A1587CA0ED9C",
              "ids": ["10-1-2-F-14"]
            }]
            }
        elif type(request) == ucoin.pks.Lookup:
            return user_keys[ get_args['search'] ]
        else:
            assert 0

    mock_network = Mock(spec=CommunityNetwork, request=community_request)
    mock = Mock(spec=Community, network=mock_network, currency="test_currency")
    return mock


@pytest.fixture
def mock_communities():
    mock = Mock(spec=Communities, communities_list=[])
    return mock


class Test_Account:
    def test_account_create1(self, mock_communities):
        account = Account.create("25500A07", "TestUser", mock_communities)
        assert account is not None

    def test_account_create2(self, monkeypatch, mock_communities, mock_community):
        monkeypatch.setattr(gnupg, 'GPG', mock_gpg)
        mock_communities.communities_list=[mock_community]
        account = Account.create("25500A07", "TestUser", mock_communities)
        assert account is not None

    def test_account_load(self):
        pass

    def test_account_add_contact(self):
        pass

    def test_account_fingerprint(self,  monkeypatch, mock_communities):
        monkeypatch.setattr(gnupg, 'GPG', mock_gpg)
        account = Account.create("25500A07", "TestUser", mock_communities)
        assert account.fingerprint() == "2E69197FAB029D8669EF85E82457A1587CA0ED9C"

    def test_account_transactions_received(self, monkeypatch, mock_community, mock_communities):
        monkeypatch.setattr(gnupg, 'GPG', mock_gpg)
        mock_communities.communities_list=[mock_community]
        account = Account.create("25500A07", "TestUser", mock_communities)
        assert len(account.transactions_received()) == 1
        assert sum( trx.value() for trx in account.transactions_received()) == 200

    def test_account_transactions_sent(self, monkeypatch, mock_community, mock_communities):
        monkeypatch.setattr(gnupg, 'GPG', mock_gpg)
        mock_communities.communities_list=[mock_community]
        account = Account.create("25500A07", "TestUser", mock_communities)
        assert len(account.transactions_sent()) == 1
        assert sum( trx.value() for trx in account.transactions_sent()) == 200

    def test_account_issued_last_dividend(self):
        pass

    def test_account_issue_dividend(self):
        pass

    def test_account_transfer_coins(self):
        pass

    def test_account_push_tht(self):
        pass

    def test_account_pull_tht(self):
        pass

