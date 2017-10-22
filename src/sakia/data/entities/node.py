import attr
from duniterpy.documents import block_uid, endpoint
from sakia.helpers import attrs_tuple_of_str


def _tuple_of_endpoints(value):
    if isinstance(value, tuple):
        return value
    elif isinstance(value, list):
        l = [endpoint(e) for e in value]
        return tuple(l)
    elif isinstance(value, str):
        if value:
            list_of_str = value.split('\n')
            conv = []
            for s in list_of_str:
                conv.append(endpoint(s))
            return conv
        else:
            return []
    else:
        raise TypeError("Can't convert {0} to list of endpoints".format(value))


@attr.s(hash=True)
class Node:
    """

    A node can have multiple states :
    - ONLINE : The node is available for requests
    - OFFLINE: The node is disconnected
    - DESYNCED : The node is online but is desynced from the network
    - CORRUPTED : The node is corrupted, some weird behaviour is going on
    """
    MERKLE_EMPTY_ROOT = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"

    ONLINE = 1
    OFFLINE = 2
    CORRUPTED = 4

    # The currency handled by this node
    currency = attr.ib(convert=str)
    # The pubkey of the node
    pubkey = attr.ib(convert=str)
    # The endpoints of the node, in a list of Endpoint objects format
    endpoints = attr.ib(convert=_tuple_of_endpoints, cmp=False, hash=False)
    # The previous block uid in /blockchain/current
    peer_blockstamp = attr.ib(convert=block_uid, cmp=False, hash=False)
    # The uid of the owner of node
    uid = attr.ib(convert=str, cmp=False, default="", hash=False)
    # The current block uid in /blockchain/current
    current_buid = attr.ib(convert=block_uid, cmp=False, default=None, hash=False)
    # The current block time in /blockchain/current
    current_ts = attr.ib(convert=int, cmp=False, default=0, hash=False)
    # The previous block uid in /blockchain/current
    previous_buid = attr.ib(convert=block_uid, cmp=False, default=None, hash=False)
    # The state of the node in Sakia
    state = attr.ib(convert=int, cmp=False, default=OFFLINE, hash=False)
    # The version of the software in /node/summary
    software = attr.ib(convert=str, cmp=False, default="", hash=False)
    # The version of the software in /node/summary
    version = attr.ib(convert=str, cmp=False, default="", hash=False)
    # Root of the merkle peers tree, default = sha256 of empty string
    merkle_peers_root = attr.ib(convert=str, cmp=False,
                                default=MERKLE_EMPTY_ROOT, hash=False)
    # Leaves of the merkle peers tree
    merkle_peers_leaves = attr.ib(convert=attrs_tuple_of_str, cmp=False, default=tuple(), hash=False)
    # Define if this node is a root node in Sakia
    root = attr.ib(convert=bool, cmp=False, default=False, hash=False)
    # If this node is a member or not
    member = attr.ib(convert=bool, cmp=False, default=False, hash=False)
    # If this node is a member or not
    last_state_change = attr.ib(convert=int, cmp=False, default=False, hash=False)

