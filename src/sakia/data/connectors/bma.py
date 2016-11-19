from duniterpy.api import bma
import logging
import aiohttp
from aiohttp.errors import ClientError, ServerDisconnectedError
import asyncio
import random
from socket import gaierror
import jsonschema
from pkg_resources import parse_version
import attr
from sakia.errors import NoPeerAvailable


@attr.s()
class BmaConnector:
    """
    This class is used to access BMA API.
    """
    _nodes_processor = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    def filter_endpoints(self, request, nodes):
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
            endpoints += n.endpoints
        return endpoints

    async def get(self, currency, request, req_args={}, get_args={}):
        """
        Start a request to the network but don't cache its result.

        :param str currency: the currency requested
        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :return: The returned data
        """
        endpoints = self.filter_endpoints(request, self._nodes_processor.synced_nodes(currency))
        if len(endpoints) > 0:
            tries = 0
            while tries < 3:
                endpoint = random.choice(endpoints)
                try:
                    self._logger.debug("Requesting {0} on endpoint {1}".format(str(request.__name__), str(endpoint)))
                    with aiohttp.ClientSession() as session:
                        json_data = await request(endpoint.conn_handler(session), **req_args)
                        return json_data
                except (ClientError, ServerDisconnectedError, gaierror,
                        asyncio.TimeoutError, ValueError, jsonschema.ValidationError) as e:
                    self._logger.debug(str(e))
                    tries += 1
        raise NoPeerAvailable("", len(endpoints))

    async def broadcast(self, currency, request, req_args={}, post_args={}):
        """
        Broadcast data to a network.
        Sends the data to all knew nodes.

        :param str currency: the currency target
        :param request: A duniterpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param post_args: Arguments to pass to the request __post__ method
        :return: All nodes replies
        :rtype: tuple of aiohttp replies

        .. note:: If one node accept the requests (returns 200),
        the broadcast should be considered accepted by the network.
        """
        filtered_endpoints = self.filter_endpoints(request, self._nodes_processor.synced_nodes(currency))
        endpoints = random.sample(filtered_endpoints, 6) if len(filtered_endpoints) > 6 else filtered_endpoints
        replies = []

        if len(endpoints) > 0:
            with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    self._logger.debug("Trying to connect to : " + str(endpoint))
                    conn_handler = endpoint.conn_handler()
                    req = request(conn_handler, **req_args)
                    reply = asyncio.ensure_future(req.post(**post_args, session=session))
                    replies.append(reply)

                try:
                    result = await asyncio.gather(*replies)
                    return tuple(result)
                except (ClientError, ServerDisconnectedError, gaierror, asyncio.TimeoutError, ValueError) as e:
                    self._logger.debug(str(e))
            return ()
        else:
            raise NoPeerAvailable("", len(endpoints))
