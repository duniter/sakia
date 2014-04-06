import pytest
import ucoinpy as ucoin
from mock import Mock
from cutecoin.models.person import Person
from cutecoin.models.community import Community


#TODO: Lookup for person after community was tested
def test_person_lookup(monkeypatch):
    pks_lookup_get = Mock(spec = ucoin.pks.Lookup.get)
    pks_lookup_get.return_value = [
    {
      "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
      "key":
      {
        "email":"misterk@supermail.com",
        "comment":"udid2;c;CAT;LOL;2000-04-19;e+43.70-079.42;0;",
        "name":"LoL Cat",
        "fingerprint":"C73882B64B7E72237A2F460CE9CAB76D19A8651E",
        "raw":"-----BEGIN PGP PUBLIC KEY BLOCK----- ... -----END PGP PUBLIC KEY BLOCK-----\r\n"
      }
    },
    {
      "signature": "-----BEGIN PGP SIGNATURE----- ... -----END PGP SIGNATURE-----",
      "key":
      {
        "email":"mistery@undermail.com",
        "comment":"udid2;c;CAT;LOL;2000-04-19;e+43.70-079.42;0;",
        "name":"LoL Cat",
        "fingerprint":"C73882B64B7E72237A2F460CE9CAB76D19A8651E",
        "raw":"-----BEGIN PGP PUBLIC KEY BLOCK----- ... -----END PGP PUBLIC KEY BLOCK-----\r\n"
      }
    }]


def test_person_jsonify():
    pass


def test_person_from_json():
    pass
