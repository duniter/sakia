from duniterpy.api import bma
import logging
from aiohttp.errors import ClientError, ServerDisconnectedError
import asyncio
import random
from socket import gaierror
import jsonschema
from pkg_resources import parse_version
import attr
from sakia.errors import NoPeerAvailable


@attr.s
class BmaConnector:
    """
    This class is used to access BMA API.
    """

    __saved_requests = [str(bma.blockchain.Block), str(bma.blockchain.Parameters)]

    _nodes_processor = attr.ib()

    def filter_nodes(self, request, nodes):
        def compare_versions(node, version):
            if node.version and node.version != '':
                try:
                    return parse_version(node.version) >= parse_version(version)
                except TypeError:
                    return False
            else:
                return True
        filters = {
            bma.ud.History: lambda n: compare_versions(n, "0.11.0"),
            bma.tx.History: lambda n: compare_versions(n, "0.11.0"),
            bma.blockchain.Membership: lambda n: compare_versions(n, "0.14")
        }
        if request in filters:
            return [n for n in nodes if filters[request](n)]
        else:
            return nodes

    async def get(self, request, req_args={}, get_args={}):
        """
        Start a request to the network but don't cache its result.

        :param class request: A bma request class calling for data
        :param dict req_args: Arguments to pass to the request constructor
        :param dict get_args: Arguments to pass to the request __get__ method
        :return: The returned data
        """
        nodes = self.filter_nodes(request, self._nodes_processor.synced_nodes)
        if len(nodes) > 0:
            tries = 0
            json_data = None
            while tries < 3:
                node = random.choice(nodes)
                nodes.pop(node)
                req = request(node.endpoint.conn_handler(), **req_args)
                try:
                    json_data = await req.get(**get_args, session=self._network.session)
                    return json_data
                except (ClientError, ServerDisconnectedError, gaierror,
                        asyncio.TimeoutError, ValueError, jsonschema.ValidationError) as e:
                    logging.debug(str(e))
                    tries += 1
        if len(nodes) == 0 or not json_data:
            raise NoPeerAvailable("", len(nodes))
        return json_data

    async def broadcast(self, request, req_args={}, post_args={}):
        """
        Broadcast data to a network.
        Sends the data to all knew nodes.

        :param request: A duniterpy bma request class
        :param req_args: Arguments to pass to the request constructor
        :param post_args: Arguments to pass to the request __post__ method
        :return: All nodes replies
        :rtype: tuple of aiohttp replies

        .. note:: If one node accept the requests (returns 200),
        the broadcast should be considered accepted by the network.
        """
        nodes = random.sample(self._nodes_processor.synced_nodes, 6) \
            if len(self._nodes_processor.synced_nodes) > 6 \
            else self._nodes_processor.synced_nodes
        replies = []
        if len(nodes) > 0:
            for node in nodes:
                logging.debug("Trying to connect to : " + node.pubkey)
                conn_handler = node.endpoint.conn_handler()
                req = request(conn_handler, **req_args)
                reply = asyncio.ensure_future(req.post(**post_args, session=self._network.session))
                replies.append(reply)
        else:
            raise NoPeerAvailable("", len(nodes))

        try:
            result = await asyncio.gather(*replies)
            return tuple(result)
        except (ClientError, ServerDisconnectedError, gaierror, asyncio.TimeoutError, ValueError) as e:
            logging.debug(str(e))
        return ()
