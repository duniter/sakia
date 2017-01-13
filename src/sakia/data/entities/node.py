import attr
from duniterpy.documents import block_uid, endpoint


def _tuple_of_endpoints(value):
    if isinstance(value, tuple):
        return value
    elif isinstance(value, list):
        l = [endpoint(e) for e in value]
        return tuple(l)
    elif isinstance(value, str):
        list_of_str = value.split('\n')
        conv = []
        for s in list_of_str:
            conv.append(endpoint(s))
        return conv
    else:
        raise TypeError("Can't convert {0} to list of endpoints".format(value))


def _tuple_of_hashes(ls):
    if isinstance(ls, tuple):
        return ls
    elif isinstance(ls, list):
        return tuple([str(a) for a in ls])
    elif isinstance(ls, str):
        if ls:  # if string is not empty
            return tuple([str(a) for a in ls.split('\n')])
        else:
            return tuple()


@attr.s()
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
    DESYNCED = 3
    CORRUPTED = 4

    # The currency handled by this node
    currency = attr.ib(convert=str)
    # The pubkey of the node
    pubkey = attr.ib(convert=str)
    # The endpoints of the node, in a list of Endpoint objects format
    endpoints = attr.ib(convert=_tuple_of_endpoints, cmp=False)
    # The previous block uid in /blockchain/current
    peer_blockstamp = attr.ib(convert=block_uid, cmp=False)
    # The uid of the owner of node
    uid = attr.ib(convert=str, cmp=False, default="")
    # The current block uid in /blockchain/current
    current_buid = attr.ib(convert=block_uid, cmp=False, default=None)
    # The current block time in /blockchain/current
    current_ts = attr.ib(convert=int, cmp=False, default=0)
    # The previous block uid in /blockchain/current
    previous_buid = attr.ib(convert=block_uid, cmp=False, default=None)
    # The state of the node in Sakia
    state = attr.ib(convert=int, cmp=False, default=OFFLINE)
    # The version of the software in /node/summary
    software = attr.ib(convert=str, cmp=False, default="")
    # The version of the software in /node/summary
    version = attr.ib(convert=str, cmp=False, default="")
    # Root of the merkle peers tree, default = sha256 of empty string
    merkle_peers_root = attr.ib(convert=str, cmp=False,
                                default=MERKLE_EMPTY_ROOT)
    # Leaves of the merkle peers tree
    merkle_peers_leaves = attr.ib(convert=_tuple_of_hashes, cmp=False, default=tuple())
    # Define if this node is a root node in Sakia
    root = attr.ib(convert=bool, cmp=False, default=False)
    # If this node is a member or not
    member = attr.ib(convert=bool, cmp=False, default=False)

