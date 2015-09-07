from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER

bma_peering = b"""{
  "version": 1,
  "currency": "test_currency",
  "endpoints": [
    "BASIC_MERKLED_API localhost 127.0.0.1 50000"
  ],
  "status": "UP",
  "block": "30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3",
  "signature": "cXuqZuDfyHvxYAEUkPH1TQ1M+8YNDpj8kiHGYi3LIaMqEdVqwVc4yQYGivjxFMYyngRfxXkyvqBKZA6rKOulCA==",
  "raw": "Version: 1\\nType: Peer\\nCurrency: meta_brouzouf\\nPublicKey: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\\nBlock: 30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3\\nEndpoints:\\nBASIC_MERKLED_API localhost 127.0.0.1 50000\\n",
  "pubkey": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
}"""

bma_wot_add = b"""{
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uids": [
    {
      "uid": "test",
      "meta": {
        "timestamp": 1409990782
      },
      "self": "J3G9oM5AKYZNLAB5Wx499w61NuUoS57JVccTShUbGpCMjCqj9yXXqNq7dyZpDWA6BxipsiaMZhujMeBfCznzyci",
      "others": [
      ]
    }
  ]
}"""

def get_mock():
    mock = HTTPMock('127.0.0.1', 50000, timeout=FOREVER)

    mock.when('GET /network/peering')\
        .reply(body=bma_peering,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/block/0')\
        .reply(body=b"Block not found",
               status=404,
               times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/current')\
        .reply(body=b"Block not found",
               status=404,
               times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=b"No member matching this pubkey or uid",
                status=404,
                times=1,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=b"No member matching this pubkey or uid",
                status=404,
                times=1,
                headers={'Content-Type': 'application/json'})

    mock.when('POST /wot/add.*')\
        .reply(body=bma_wot_add,
               status=200,
               times=FOREVER,
               headers={'Content-Type': 'application/json'})
    return mock
