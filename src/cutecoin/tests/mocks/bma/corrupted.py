import json
import time
from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER

bma_memberships_empty_array = {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "uid": "john",
    "sigDate": 123456789,
    "memberships": [ ]
}


def get_mock():
    mock = HTTPMock('127.0.0.1', 50000)

    mock.when('GET /blockchain/memberships/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
        .reply(body=bytes(json.dumps(bma_memberships_empty_array), "utf-8"),
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    return mock
