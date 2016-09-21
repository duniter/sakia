import attr
import json
from duniterpy.documents import block_uid, endpoint


def _list_of_endpoints(value):
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        list_of_str = value.split('\n')
        conv = []
        for s in list_of_str:
            conv.append(endpoint(s))
        return conv
    else:
        raise TypeError("Can't convert {0} to list of endpoints".format(value))


def _merkle_nodes(value):
    if isinstance(value, dict):
        return value
    elif isinstance(value, str):
        return json.loads(value)
    else:
        raise TypeError("Can't convert {0} to merkle nodes tree".format(value))


@attr.s()
class Node:
    ONLINE = 1
    OFFLINE = 2
    DESYNCED = 3
    CORRUPTED = 4

    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    endpoints = attr.ib(convert=_list_of_endpoints, cmp=False)
    current_buid = attr.ib(convert=block_uid, cmp=False)
    previous_buid = attr.ib(convert=block_uid, cmp=False)
    state = attr.ib(convert=int, cmp=False)
    software = attr.ib(convert=str, cmp=False)
    version = attr.ib(convert=str, cmp=False)
    merkle_nodes = attr.ib(convert=_merkle_nodes, cmp=False)

