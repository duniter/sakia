import pytest
import ucoinpy as ucoin
from mock import Mock, MagicMock
from cutecoin.models.person import Person
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

@pytest.fixture
def mock_community():
    def community_request(request, get_args={}):
        return user_keys[ get_args['search'] ]
    mock_network = Mock(spec=CommunityNetwork, request=community_request)
    community = MagicMock(spec=Community, network=mock_network)

    return community
    
#TODO: Lookup for person after community was tested
class Test_Person():
    def test_person_lookup(self, monkeypatch, mock_community):
        person = Person.lookup("2E69197FAB029D8669EF85E82457A1587CA0ED9C", mock_community)
        assert person.name == "Mister test2"
        assert person.fingerprint == "2E69197FAB029D8669EF85E82457A1587CA0ED9C"
        assert person.email == "mistertest2@testmail.com"

    def test_person_jsonify(self):
        pass

    def test_person_from_json(self):
        pass
