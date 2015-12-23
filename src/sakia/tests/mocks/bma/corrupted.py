import json
from ..server import MockServer

bma_memberships_empty_array = {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "uid": "john",
    "sigDate": 123456789,
    "memberships": [ ]
}


bma_null_data = {
  "certifications": [
    {
      "written": {
      },
    },
    {
      "written": None,
    }
  ]
}

def get_mock(loop):
    mock = MockServer(loop)

    mock.add_route('GET', '/blockchain/memberships/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_memberships_empty_array)

    return mock
