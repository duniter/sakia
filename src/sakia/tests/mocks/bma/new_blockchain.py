from ..server import MockServer


bma_wot_add = {
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
}

def get_mock(loop):
    mock = MockServer(loop)

    mock.add_route('GET', '/blockchain/block/0', {'message': "Block not found"}, 404)

    mock.add_route('GET', '/blockchain/current', {'message': "Block not found"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',
                   {'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',
                   {'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/john',
                   {'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/doe',
                   {'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('POST', '/wot/add', bma_wot_add, 200)
    return mock
