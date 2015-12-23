
from ..server import MockServer


bma_lookup_test_john = {
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

bma_lookup_test_doe = {
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

bma_lookup_test_patrick = {
  "partial": False,
  "results": [
    {
      "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
      "uids": [
        {
          "uid": "patrick",
          "meta": {
            "timestamp": 1441130831
          },
          "self": "QNX2HDAxcHawc47TnMqb5/ou2lwa+zYOyeNk0a52dQDJX/NWmeTzGfTjdCtjpXmSCuPSg0F1mOnLQVd60xAzDA==",
          "others": []
        }
      ],
      "signed": []
    }
  ]
}


def get_mock(loop):
    mock = MockServer(loop)

    mock.add_route('GET', '/blockchain/block/0', {"message": "Block not found"}, 404)

    mock.add_route('GET', '/blockchain/current', {'message': "Block not found"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',
                   {'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/john', bma_lookup_test_john, 200)

    mock.add_route('GET', '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_lookup_test_john, 200)

    mock.add_route('GET', '/wot/lookup/doe', bma_lookup_test_doe, 200)

    mock.add_route('GET', '/wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn', bma_lookup_test_doe, 200)

    mock.add_route('GET', '/wot/lookup/patrick', bma_lookup_test_patrick, 200)

    mock.add_route('GET', '/wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn', bma_lookup_test_patrick, 200)

    mock.add_route('POST', '/wot/add', {}, 200)

    return mock
