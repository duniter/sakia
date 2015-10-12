from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtNetwork import QNetworkReply
from ucoinpy.api.bma import blockchain
from ucoinpy.documents import Block, BlockId
from .....tools.exceptions import NoPeerAvailable
from ..... import __version__
import logging
from aiohttp.errors import ClientError
import asyncio
import random


class BmaAccess(QObject):
    """
    This class is used to access BMA API.
    """

    __saved_requests = [str(blockchain.Block), str(blockchain.Parameters)]

    def __init__(self, data, network):
        """
        Constructor of a network

        :param dict data: The data present in this cache
        :param cutecoin.core.net.network.Network network: The network used to connect
        """
        super().__init__()
        self._data = data
        self._rollback_to = None
        self._pending_requests = {}
        self._network = network

    @classmethod
    def create(cls, network):
        """
        Initialize a new BMAAccess object with empty data.

        :param cutecoin.core.net.network.Network network:
        :return: A new BmaAccess object
        :rtype: cutecoin.core.net.api.bma.access.BmaAccess
        """
        return cls({}, network)

    @property
    def data(self):
        return self._data.copy()

    def load_from_json(self, json_data):
        """
        Put data in the cache from json datas.

        :param dict data: The cache in json format
        """
        data = {}
        for entry in json_data['entries']:
            key = entry['key']
            cache_key = (key[0], key[1], key[2], key[3], key[4])
            data[cache_key] = entry['value']
        self._data = data
        self._rollback_to = json_data['rollback']

    def jsonify(self):
        """
        Get the cache in json format

        :return: The cache as a dict in json format
        """
        data = {k: self._data[k] for k in self._data.keys()}
        entries = []
        for d in data:
            entries.append({'key': d,
                            'value': data[d]})
        return {'rollback': self._rollback_to,
                'entries': entries}

    @staticmethod
    def _gen_cache_key(request, req_args, get_args):
        return (str(request),
                str(tuple(frozenset(sorted(req_args.keys())))),
                str(tuple(frozenset(sorted(req_args.values())))),
                str(tuple(frozenset(sorted(get_args.keys())))),
                str(tuple(frozenset(sorted(get_args.values())))))

    def _compare_json(self, first, second):
        """
        Compare two json dicts
        :param first: the first dictionnary
        :param second: the second dictionnary
        :return: True if the json dicts are the same
        :rtype: bool
        """
        def ordered(obj):
            if isinstance(obj, dict):
                return sorted((k, ordered(v)) for k, v in obj.items())
            if isinstance(obj, list):
                return sorted(ordered(x) for x in obj)
            else:
                return obj
        return ordered(first) == ordered(second)

    def _get_from_cache(self, request, req_args, get_args):
        """
        Get data from the cache
        :param request: The requested data
        :param cache_key: The key
        :rtype: tuple[bool, dict]
        """
        cache_key = BmaAccess._gen_cache_key(request, req_args, get_args)
        if cache_key in self._data.keys():
            cached_data = self._data[cache_key]
            need_reload = True
            # If we detected a rollback
            # We reload if we don't know if this block changed or not
            if self._rollback_to:
                if request is blockchain.Block:
                    if get_args["number"] >= self._rollback_to:
                        need_reload = True
                if request is blockchain.Parameters and self._rollback_to == 0:
                    need_reload = True
            elif str(request) in BmaAccess.__saved_requests \
                or cached_data['metadata']['block_hash'] == self._network.current_blockid.sha_hash:
                need_reload = False
            ret_data = cached_data['value']
        else:
            need_reload = True
            ret_data = None
        return need_reload, ret_data

    def _update_rollback(self, request, req_args, get_args, data):
        """
        Update the rollback
        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :param dict data: Json data got from the blockchain
        """
        if self._rollback_to and request is blockchain.Block:
            if get_args['number'] >= self._rollback_to:
                cache_key = BmaAccess._gen_cache_key(request, req_args, get_args)
                if cache_key in self._data and self._data[cache_key]['value']['hash'] == data['hash']:
                    self._rollback_to = get_args['number']

    def _update_cache(self, request, req_args, get_args, data):
        """
        Update data in cache and returns True if cached data changed
        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :param dict data: Json data to save in cache
        :return: True if data changed
        :rtype: bool
        """
        self._update_rollback(request, req_args, get_args, data)

        cache_key = BmaAccess._gen_cache_key(request, req_args, get_args)
        if cache_key not in self._data:
            self._data[cache_key] = {'metadata': {},
                                     'value': {}}

        self._data[cache_key]['metadata']['block_number'] = self._network.current_blockid.number
        self._data[cache_key]['metadata']['block_hash'] = self._network.current_blockid.sha_hash
        self._data[cache_key]['metadata']['cutecoin_version'] = __version__
        if not self._compare_json(self._data[cache_key]['value'], data):
            self._data[cache_key]['value'] = data
            return True
        return False

    @asyncio.coroutine
    def future_request(self, request, req_args={}, get_args={}):
        """
        Start a request to the network and returns a future.

        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :return: The future data
        :rtype: dict
        """
        data = self._get_from_cache(request, req_args, get_args)
        need_reload = data[0]
        json_data = data[1]

        nodes = self._network.synced_nodes
        if need_reload and len(nodes) > 0:
            tries = 0
            while tries < 3:
                node = random.choice(nodes)
                conn_handler = node.endpoint.conn_handler()
                req = request(conn_handler, **req_args)
                try:
                    json_data = yield from req.get(**get_args)
                    self._update_cache(request, req_args, get_args, json_data)
                    return json_data
                except ValueError as e:
                    if '404' in str(e) or '400' in str(e):
                        raise
                    tries += 1
                except ClientError:
                    tries += 1
                except asyncio.TimeoutError:
                    tries += 1
        if len(nodes) == 0 or json_data is None:
            raise NoPeerAvailable("", len(nodes))
        return json_data

    @asyncio.coroutine
    def simple_request(self, request, req_args={}, get_args={}):
        """
        Start a request to the network but don't cache its result.

        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :return: The returned data if cached = True else return the QNetworkReply
        """
        nodes = self._network.synced_nodes
        if len(nodes) > 0:
            node = random.choice(nodes)
            req = request(node.endpoint.conn_handler(), **req_args)
            tries = 0
            while tries < 3:
                try:
                    json_data = yield from req.get(**get_args)
                    return json_data
                except ValueError as e:
                    if '404' in str(e) or '400' in str(e):
                        raise
                    tries += 1
                except ClientError:
                    tries += 1
                except asyncio.TimeoutError:
                    tries += 1
        else:
            raise NoPeerAvailable("", len(nodes))

    @asyncio.coroutine
    def broadcast(self, request, req_args={}, post_args={}):
        """
        Broadcast data to a network.
        Sends the data to all knew nodes.

        :param request: A ucoinpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param post_args: Arguments to pass to the request __post__ method
        :return: All nodes replies
        :rtype: tuple of QNetworkReply

        .. note:: If one node accept the requests (returns 200),
        the broadcast should be considered accepted by the network.
        """
        nodes = self._network.online_nodes
        replies = []
        if len(nodes) > 0:
            for node in nodes:
                logging.debug("Trying to connect to : " + node.pubkey)
                conn_handler = node.endpoint.conn_handler()
                req = request(conn_handler, **req_args)
                try:
                    reply = yield from req.post(**post_args)
                    replies.append(reply)
                except ValueError as e:
                    if '404' in str(e) or '400' in str(e):
                        raise
                except ClientError:
                    pass
                except asyncio.TimeoutError:
                    pass
        else:
            raise NoPeerAvailable("", len(nodes))
        return tuple(replies)
