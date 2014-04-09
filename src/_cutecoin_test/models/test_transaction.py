import pytest
import re
import ucoinpy as ucoin
from mock import Mock, MagicMock
from cutecoin.models.transaction import Transaction, Transfer, Issuance
from cutecoin.models.transaction import factory
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

def community_request_issuance(request, get_args={}):
    if type(request) == ucoin.hdc.transactions.View:
        return {
          "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
          "raw": "Version: 1\r\n...\r\n",
          "transaction":
          {
            "version": 1,
            "currency": "beta_brousouf",
            "sender": "31A6302161AC8F5938969E85399EB3415C237F93",
            "number": 1,
            "previousHash": "BE522363749E62BA1034C7B1358B01C75289DA48",
            "recipient": "31A6302161AC8F5938969E85399EB3415C237F93",
            "type": "ISSUANCE",
            "coins": [
             {
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
    elif type(request) == ucoin.pks.Lookup:
        return user_keys[ get_args['search'] ]
    else:
        assert 0
        
        
def community_request_transfer(request, get_args={}):
    if type(request) == ucoin.hdc.transactions.View:
        return {
            "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
            "raw": "Version: 1\r\n...\r\n",
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
    elif type(request) == ucoin.pks.Lookup:
        return user_keys[ get_args['search'] ]
    else:
        assert 0


def mock_community(community_request):
    mock_network = Mock(spec=CommunityNetwork, request=community_request)
    community = MagicMock(spec=Community, network=mock_network)

    return community
    

class Test_Transaction:
    def test_create_transaction_issuance(self):
        community = mock_community( community_request_issuance )
        trx = factory.create_transaction("31A6302161AC8F5938969E85399EB3415C237F93", 1, community)
        assert trx is not None
        assert type(trx) is Issuance
        
    def test_create_transaction_transfer(self):
        community = mock_community( community_request_transfer )
        trx = factory.create_transaction("31A6302161AC8F5938969E85399EB3415C237F93", 15, community)
        assert trx is not None
        assert type(trx) is Transfer
        
    def test_transaction_value(self):
        community = mock_community( community_request_issuance )
        trx = factory.create_transaction("31A6302161AC8F5938969E85399EB3415C237F93", 1, community)
        assert trx.value() == 100
        
    def test_transaction_currency(self):
        community = mock_community( community_request_issuance )
        trx = factory.create_transaction("31A6302161AC8F5938969E85399EB3415C237F93", 1, community)
        assert trx.currency() == "beta_brousouf"
