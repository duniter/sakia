import logging
import aiohttp
from aiohttp import ClientError
from duniterpy.api import bma, errors
from duniterpy.documents import BMAEndpoint, SecuredBMAEndpoint
from sakia.errors import NoPeerAvailable
from pkg_resources import parse_version
from socket import gaierror
import asyncio
import random
import jsonschema
import attr
import copy


async def parse_responses(responses):
    result = (False, "")
    for r in responses:
        try:
            if not result[0]:
                if isinstance(r, BaseException):
                    result = (False, str(r))
                elif r.status == 400:
                    error = await r.text()
                    try:
                        result = (False, errors.DuniterError(bma.parse_error(error)).message)
                    except jsonschema.ValidationError:
                        result = (False, error)
                elif r.status == 200:
                    result = (True, (await r.json()))
                elif not result[0]:
                    result = (False, (await r.text()))
            else:
                await r.release()
        except Exception as e:
            if not result[0]:
                result = (False, str(e))
    return result

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


def make_hash(o):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """

    if isinstance(o, (set, tuple, list)):
        return tuple(sorted([make_hash(e) for e in o]))
    elif not isinstance(o, dict):
        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)

    return hash(tuple(frozenset(sorted(new_o.items()))))


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


def _filter_data(request, data):
    filtered = data
    if request is bma.tx.history:
        filtered = copy.deepcopy(data)
        filtered["history"].pop("sending")
        filtered["history"].pop("receiving")
        filtered["history"].pop("pending")
    elif request is bma.wot.requirements:
        filtered = copy.deepcopy(data)
        for idty in filtered["identities"]:
            for c in idty["certifications"]:
                c.pop("expiresIn")
            idty.pop('membershipPendingExpiresIn')

    return filtered


def _merge_lookups(answers_data):
    if len(answers_data) == 1:
        data = next((v for v in answers_data.values()))
        if isinstance(data, errors.DuniterError):
            raise data

    lookup_data = {"partial": False,
                   "results": []}
    for dict_hash in answers_data:
        if not isinstance(answers_data[dict_hash], errors.DuniterError):
            for data in answers_data[dict_hash]["results"]:
                lookup_data["results"].append(data)
    return lookup_data


def _best_answer(answers, answers_data, nb_verification):
    best_dict_hash = next(k for k in answers.keys())
    best_dict_hash_score = len(answers[best_dict_hash])
    for dict_hash in answers:
        if len(answers[dict_hash]) > best_dict_hash_score:
            best_dict_hash = dict_hash
            best_dict_hash_score = len(answers[dict_hash])
        if len(answers[dict_hash]) >= nb_verification:
            if isinstance(answers_data[dict_hash], errors.DuniterError):
                raise answers_data[dict_hash]
            else:
                return answers_data[dict_hash]
    if isinstance(answers_data[best_dict_hash], errors.DuniterError):
        raise answers_data[best_dict_hash]
    else:
        return answers_data[best_dict_hash]


@attr.s()
class BmaConnector:
    """
    This class is used to access BMA API.
    """
    _nodes_processor = attr.ib()
    _user_parameters = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    async def verified_get(self, currency, request, req_args):
        synced_nodes = self._nodes_processor.synced_members_nodes(currency)
        if not synced_nodes:
            # If no node is known as a member, lookup synced nodes as a fallback
            synced_nodes = self._nodes_processor.synced_nodes(currency)
        nodes_generator = (n for n in synced_nodes)
        answers = {}
        answers_data = {}
        nb_verification = min(max(1, 0.66 * len(synced_nodes)), 10)
        # We try to find agreeing nodes from one 1 to 66% of nodes, max 10
        session = aiohttp.ClientSession()
        filtered_data = {}
        try:
            while max([len(nodes) for nodes in answers.values()] + [0]) <= nb_verification:
                futures = []

                try:
                    for i in range(0, int(nb_verification)+1):
                        node = next(nodes_generator)
                        endpoints = filter_endpoints(request, [node])
                        if not endpoints:
                            continue
                        endpoint = random.choice(endpoints)
                        self._logger.debug(
                            "Requesting {0} on endpoint {1}".format(str(request.__name__), str(endpoint)))
                        futures.append(request(next(
                            endpoint.conn_handler(session, proxy=self._user_parameters.proxy())),
                            **req_args))
                except StopIteration:
                    # When no more node is available, we go out of the while loop
                    break
                finally:
                    # Everytime we go out of the while loop, we gather the futures
                    if futures:
                        responses = await asyncio.gather(*futures, return_exceptions=True)
                        for r in responses:
                            if isinstance(r, errors.DuniterError):
                                if r.ucode == errors.HTTP_LIMITATION:
                                    self._logger.debug("Exception in responses : " + r.message)
                                    continue
                                else:
                                    data_hash = hash(r.ucode)
                            elif isinstance(r, BaseException):
                                self._logger.debug("Exception in responses : " + str(r))
                                continue
                            else:
                                filtered_data = _filter_data(request, r)
                                data_hash = make_hash(filtered_data)
                            answers_data[data_hash] = r
                            if data_hash not in answers:
                                answers[data_hash] = [node]
                            else:
                                answers[data_hash].append(node)
        finally:
            await session.close()

        if len(answers_data) > 0:
            if request is bma.wot.lookup:
                return _merge_lookups(answers_data)
            else:
                return _best_answer(answers, answers_data, nb_verification)

        raise NoPeerAvailable("", len(synced_nodes))

    async def simple_get(self, currency, request, req_args):
        endpoints = filter_endpoints(request, self._nodes_processor.synced_nodes(currency))
        tries = 0
        while tries < 3 and endpoints:
            endpoint = random.choice(endpoints)
            endpoints.remove(endpoint)
            try:
                self._logger.debug("Requesting {0} on endpoint {1}".format(str(request.__name__), str(endpoint)))
                async with aiohttp.ClientSession() as session:
                    json_data = await request(next(endpoint.conn_handler(session), **req_args))
                    return json_data
            except errors.DuniterError as e:
                if e.ucode == errors.HTTP_LIMITATION:
                    self._logger.debug(str(e))
                    tries += 1
                else:
                    raise
            except (ClientError, gaierror, asyncio.TimeoutError,
                    ValueError, jsonschema.ValidationError) as e:
                self._logger.debug(str(e))
                tries += 1
        raise NoPeerAvailable("", len(endpoints))

    async def get(self, currency, request, req_args={}, verify=True):
        """
        :param str currency: the currency requested
        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param bool verify: Verify returned value against multiple nodes
        :return: The returned data
        """
        if verify:
            return await self.verified_get(currency, request, req_args)
        else:
            return await self.simple_get(currency, request, req_args)

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
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    self._logger.debug("Trying to connect to : " + str(endpoint))
                    reply = asyncio.ensure_future(request(next(endpoint.conn_handler(session,
                                                                                proxy=self._user_parameters.proxy())),
                                                          **req_args))
                    replies.append(reply)

                result = await asyncio.gather(*replies, return_exceptions=True)
                return tuple(result)
        else:
            raise NoPeerAvailable("", len(endpoints))
