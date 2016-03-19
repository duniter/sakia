from ..server import MockServer
from ucoinpy.api import errors

bma_wot_add = {
  "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
  "uids": [
    {
      "uid": "test",
      "meta": {
        "timestamp": "0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
      },
      "self": "J3G9oM5AKYZNLAB5Wx499w61NuUoS57JVccTShUbGpCMjCqj9yXXqNq7dyZpDWA6BxipsiaMZhujMeBfCznzyci",
      "others": [
      ],
    "revocation_sig": "CTmlh3tO4B8f8IbL8iDy5ZEr3jZDcxkPmDmRPQY74C39MRLXi0CKUP+oFzTZPYmyUC7fZrUXrb3LwRKWw1jEBQ==",
    "revoked": False,
    }
  ]
}

bma_parameters = {
    "currency": "test_currency",
    "c": 0.1,
    "dt": 86400,
    "ud0": 100,
    "sigPeriod": 600,
    "sigValidity": 2629800,
    "sigQty": 3,
    "xpercent": 0.9,
    "sigStock": 10,
    "sigWindow": 1000,
    "msValidity": 2629800,
    "stepMax": 3,
    "medianTimeBlocks": 11,
    "avgGenTime": 600,
    "dtDiffEval": 20,
    "blocksRot": 144,
    "percentRot": 0.67
}

def get_mock(loop):
    mock = MockServer(loop)

    mock.add_route('GET', '/blockchain/parameters', bma_parameters, 200)

    mock.add_route('GET', '/blockchain/block/0', {'ucode': errors.BLOCK_NOT_FOUND,
                                                  'message': "Block not found"}, 404)

    mock.add_route('GET', '/blockchain/current', {'ucode': errors.NO_CURRENT_BLOCK,
                                                  'message': "Block not found"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID,
                    'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',
                   {'ucode': errors.NO_MATCHING_IDENTITY,
                    'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/john',
                   {'ucode': errors.NO_MATCHING_IDENTITY,
                    'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/john',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/doe',
                   {'ucode': errors.NO_MATCHING_IDENTITY,
                    'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/doe',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('POST', '/wot/add', bma_wot_add, 200)

    mock.add_route('POST', '/wot/certify', {}, 200)
    return mock
