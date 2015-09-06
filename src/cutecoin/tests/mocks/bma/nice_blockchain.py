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

bma_lookup_john = b"""{
  "partial": false,
  "results": [
    {
      "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
      "uids": [
        {
          "uid": "john",
          "meta": {
            "timestamp": 1441130831
          },
          "self": "ZrHK0cCqrxWReROK0ciiSb45+dRphJa68qFaSjdve8bBdnGAu7+DIu0d+u/fXrNRXuObihOKMBIawaIVPNHqDw==",
          "others": []
        }
      ],
      "signed": []
    }
  ]
}"""

bma_lookup_doe = b"""{
  "partial": false,
  "results": [
    {
      "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
      "uids": [
        {
          "uid": "doe",
          "meta": {
            "timestamp": 1441130831
          },
          "self": "cIkHPQQ5+xTb4cKWv85rcYcZT+E3GDtX8B2nCK9Vs12p2Yz4bVaZiMvBBwisAAy2WBOaqHS3ydpXGtADchOICw==",
          "others": []
        }
      ],
      "signed": []
    }
  ]
}"""

bma_certifiers_of_john = b"""{
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uid": "john",
  "isMember": true,
  "certifications": [
  ]
}"""

bma_certified_by_john = b"""{
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uid": "john",
  "isMember": true,
  "certifications": [
  ]
}"""


def get_mock():
    mock = HTTPMock('127.0.0.1', 50000)

    mock.when('GET /network/peering')\
        .reply(body=bma_peering,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bma_certifiers_of_john,
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bma_certified_by_john,
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/john')\
            .reply(body=bma_lookup_john,
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bma_lookup_john,
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/doe')\
            .reply(body=bma_lookup_doe,
                status=200,
                times=1,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')\
            .reply(body=bma_lookup_doe,
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})


    return mock
