import json
from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER

bma_peering = {
  "version": 1,
  "currency": "test_currency",
  "endpoints": [
    "BASIC_MERKLED_API localhost 127.0.0.1 50000"
  ],
  "status": "UP",
  "block": "30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3",
  "signature": "cXuqZuDfyHvxYAEUkPH1TQ1M+8YNDpj8kiHGYi3LIaMqEdVqwVc4yQYGivjxFMYyngRfxXkyvqBKZA6rKOulCA==",
  "raw": "Version: 1\nType: Peer\nCurrency: meta_brouzouf\nPublicKey: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nBlock: 30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3\nEndpoints:\nBASIC_MERKLED_API localhost 127.0.0.1 50000\n",
  "pubkey": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
}

bma_lookup_john = {
  "partial": False,
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
}

bma_lookup_doe = {
  "partial": False,
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
}

bma_certifiers_of_john = {
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uid": "john",
  "isMember": True,
  "certifications": [
  ]
}

bma_certified_by_john = {
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uid": "john",
  "isMember": True,
  "certifications": [
  ]
}

bma_parameters = {
    "currency": "test_currency",
    "c": 0.1,
    "dt": 86400,
    "ud0": 100,
    "sigDelay": 604800,
    "sigValidity": 2629800,
    "sigQty": 3,
    "sigWoT": 3,
    "msValidity": 2629800,
    "stepMax": 3,
    "medianTimeBlocks": 11,
    "avgGenTime": 600,
    "dtDiffEval": 20,
    "blocksRot": 144,
    "percentRot": 0.67
}

bma_blockchain_current = {
    "version": 1,
    "nonce": 6909,
    "number": 15,
    "powMin": 4,
    "time": 1441618206,
    "medianTime": 1441614759,
    "membersCount": 20,
    "monetaryMass": 11711349901120,
    "currency": "test_currency",
    "issuer": "EPs9qX7HmCDy6ptUoMLpTzbh9toHu4au488pBTU9DN6y",
    "signature": "kz/34w1cG+8tYacuPXf3FPmsFwrvtWkwp1POLJuX1P0zYaB9Tuu7iyYJzMQS0Xa3vwuWRqfz+fgyoCGnBjBLBQ==",
    "hash": "0000CB4E9CCDE6F579135331C97F13903E8B6E21",
    "parameters": "",
    "previousHash": "00003BDA844D77EEE7CF32A6C3C87F2ACBFCFCBB",
    "previousIssuer": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
    "dividend": None,
    "membersChanges": [ ],
    "identities": [ ],
    "joiners": [ ],
    "actives": [ ],
    "leavers": [ ],
    "excluded": [ ],
    "certifications": [ ],
    "transactions": [ ],
    "raw": "Version: 1\nType: Block\nCurrency: meta_brouzouf\nNonce: 6909\nNumber: 30898\nPoWMin: 4\nTime: 1441618206\nMedianTime: 1441614759\nIssuer: EPs9qX7HmCDy6ptUoMLpTzbh9toHu4au488pBTU9DN6y\nPreviousHash: 00003BDA844D77EEE7CF32A6C3C87F2ACBFCFCBB\nPreviousIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nMembersCount: 20\nIdentities:\nJoiners:\nActives:\nLeavers:\nExcluded:\nCertifications:\nTransactions:\n"
}

# Sent 6, received 20 + 30
bma_txhistory_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "history":
    {
        "sent":
    [
    {
        "version": 1,
        "issuers":
        [
            "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        ],
        "inputs":
        [
            "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
        ],
        "outputs":
        [
            "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:2",
            "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:6"
        ],
        "comment": "",
        "signatures":
        [
            "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
        ],
        "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
        "block_number": 2,
        "time": 1421932545
    },
],
"received":
    [
        {
            "version": 1,
            "issuers":
            [
                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
            ],
            "inputs":
            [
                "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
            ],
            "outputs":
            [
                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:2",
                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:20"
            ],
            "comment": "",
            "signatures":
            [
                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
            ],
            "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
            "block_number": 2,
            "time": 1421932545
        },
        {
            "version": 1,
            "issuers":
            [
                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
            ],
            "inputs":
            [
                "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
            ],
            "outputs":
            [
                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:5",
                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:40"
            ],
            "comment": "",
            "signatures":
            [
                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
            ],
            "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
            "block_number": 12,
            "time": 1421932454
        }
        ],
        "sending": [ ],
        "receiving": [ ]
    }
}

bma_udhistory_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "history":
{
    "history":
    [
    {
        "block_number": 2,
        "consumed": False,
        "time": 1435749971,
        "amount": 5
    },
    {

        "block_number": 10,
        "consumed": False,
        "time": 1435836032,
        "amount": 10

    }
    ]
}}

bma_txsources_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "sources":
[
{
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "type": "D",
    "number": 2,
    "fingerprint": "4A317E3D676E9800E1E92AA2A7255BCEEFF31185",
    "amount": 7
},
    {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "type": "D",
    "number": 4,
    "fingerprint": "4A317E3D676E9800E1E92AA2A7255BCEEFF31185",
    "amount": 9
}
]}


def get_mock():
    mock = HTTPMock('127.0.0.1', 50000)

    mock.when('GET /network/peering')\
        .reply(body=bytes(json.dumps(bma_peering), "utf-8"),
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/parameters')\
            .reply(body=bytes(json.dumps(bma_parameters), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/current')\
            .reply(body=bytes(json.dumps(bma_blockchain_current), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/block/15')\
            .reply(body=bytes(json.dumps(bma_blockchain_current), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /tx/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ/blocks/0/99')\
            .reply(body=bytes(json.dumps(bma_txhistory_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /tx/sources/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bytes(json.dumps(bma_txsources_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})


    mock.when('GET /ud/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bytes(json.dumps(bma_udhistory_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bytes(json.dumps(bma_certifiers_of_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bytes(json.dumps(bma_certified_by_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/john')\
            .reply(body=bytes(json.dumps(bma_lookup_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')\
            .reply(body=bytes(json.dumps(bma_lookup_john), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/doe')\
            .reply(body=bytes(json.dumps(bma_lookup_doe), "utf-8"),
                status=200,
                times=1,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')\
            .reply(body=bytes(json.dumps(bma_lookup_doe), "utf-8"),
                status=200,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /wot/certifiers-of/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')\
            .reply(body=b"No member matching this pubkey or uid",
                status=404,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    mock.when('GET /blockchain/memberships/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')\
            .reply(body=b"No member matching this pubkey or uid",
                status=404,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    return mock
