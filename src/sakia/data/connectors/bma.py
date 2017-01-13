import logging
import aiohttp
from aiohttp.errors import ClientError, ServerDisconnectedError
from duniterpy.api import bma
from duniterpy.documents import BMAEndpoint, SecuredBMAEndpoint
from sakia.errors import NoPeerAvailable
from pkg_resources import parse_version
from socket import gaierror
import asyncio
import random
import jsonschema
import attr
import dpath
import copy


def make_hash(o):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """

    if isinstance(o, (set, tuple, list)):
        return tuple([make_hash(e) for e in o])
    elif not isinstance(o, dict):
        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)

    return hash(tuple(frozenset(sorted(new_o.items()))))


def filter_endpoints(request, nodes):
    def compare_versions(node, version):
        if node.version and node.version != '':
            try:
                return parse_version(node.version) >= parse_version(version)
            except TypeError:
                return False
        else:
            return True
    filters = {
        bma.ud.history: lambda n: compare_versions(n, "0.11.0"),
        bma.tx.history: lambda n: compare_versions(n, "0.11.0"),
        bma.blockchain.membership: lambda n: compare_versions(n, "0.14")
    }
    if request in filters:
        nodes = [n for n in nodes if filters[request](n)]
    endpoints = []
    for n in nodes:
        endpoints += [e for e in n.endpoints if type(e) in (BMAEndpoint, SecuredBMAEndpoint)]
    return endpoints


def _compare_json(first, second):
    """
    Compare two json dicts
    :param first: the first dictionnary
    :param second: the second dictionnary
    :return: True if the json dicts are the same
    :rtype: bool
    """

    def ordered(obj):
        if isinstance(obj, dict):
            try:
                return sorted((k, ordered(v)) for k, v in obj.items())
            except TypeError:
                return obj
        if isinstance(obj, list):
            try:
                return sorted(ordered(x) for x in obj)
            except TypeError:
                return obj
        else:
            return obj

    return ordered(first) == ordered(second)


def _filter_blockchain_data(request, data):
    """

    :param request:
    :param dict data:
    :return:
    """
    include_only = {
        bma.wot.lookup: "",
        bma.tx.history: "/history/[send|received]"
    }
    if request in include_only:
        data = dpath.util.search(data, include_only[request])
    return data

@attr.s()
class BmaConnector:
    """
    This class is used to access BMA API.
    """
    _nodes_processor = attr.ib()
    _user_parameters = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    async def get(self, currency, request, req_args={}, verify=True):
        """
        Start a request to the network but don't cache its result.

        :param str currency: the currency requested
        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param bool verify: Verify returned value against multiple nodes
        :return: The returned data
        """
        synced_nodes = self._nodes_processor.synced_nodes(currency)
        nodes_generator = (n for n in synced_nodes)
        answers = {}
        answers_data = {}
        nb_verification = min(max(1, 0.66*len(synced_nodes)), 10)
        try:
            # On chercher des reponses jusqu'a obtenir un nombre de noeuds d'accords de 1 à 66% des noeuds, max 10
            while max([len(ans) for ans in answers.values()] + [0]) <= nb_verification:
                node = next(nodes_generator)
                endpoints = filter_endpoints(request, [node])
                tries = 0
                while tries < 3 and endpoints:
                    endpoint = random.choice(endpoints)
                    endpoints.remove(endpoint)
                    try:
                        self._logger.debug("Requesting {0} on endpoint {1}".format(str(request.__name__), str(endpoint)))
                        async with aiohttp.ClientSession() as session:
                            json_data = await request(endpoint.conn_handler(session, proxy=self._user_parameters.proxy()),
                                                      **req_args)
                            if verify:
                                filtered_data = _filter_blockchain_data(request, json_data)
                                data_hash = make_hash(filtered_data)
                                answers_data[data_hash] = json_data
                                if data_hash not in answers:
                                    answers[data_hash] = [node]
                                else:
                                    answers[data_hash].append(node)
                                break
                            else:
                                return json_data
                    except (ClientError, ServerDisconnectedError, gaierror,
                            asyncio.TimeoutError, ValueError, jsonschema.ValidationError) as e:
                        self._logger.debug(str(e))
                        tries += 1
        except StopIteration:
            pass

        for dict_hash in answers:
            if len(answers[dict_hash]) >= nb_verification:
                return answers_data[dict_hash]

        raise NoPeerAvailable("", len(endpoints))

    async def broadcast(self, currency, request, req_args={}):
        """
        Broadcast data to a network.
        Sends the data to all knew nodes.

        :param str currency: the currency target
        :param request: A duniterpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :return: All nodes replies
        :rtype: tuple of aiohttp replies

        .. note:: If one node accept the requests (returns 200),
        the broadcast should be considered accepted by the network.
        """
        filtered_endpoints = filter_endpoints(request, self._nodes_processor.synced_nodes(currency))
        endpoints = random.sample(filtered_endpoints, 6) if len(filtered_endpoints) > 6 else filtered_endpoints
        replies = []

        if len(endpoints) > 0:
            with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    self._logger.debug("Trying to connect to : " + str(endpoint))
                    reply = asyncio.ensure_future(request(endpoint.conn_handler(session,
                                                                                proxy=self._user_parameters.proxy()),
                                                          **req_args))
                    replies.append(reply)

                result = await asyncio.gather(*replies, return_exceptions=True)
                return tuple(result)
            return ()
        else:
            raise NoPeerAvailable("", len(endpoints))
