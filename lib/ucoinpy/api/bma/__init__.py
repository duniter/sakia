#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#


__all__ = ['api']

__author__      = 'Caner Candan'
__version__     = '0.11.0'
__nonsense__    = 'uCoin'

PROTOCOL_VERSION = "1"

import aiohttp, asyncio, logging, json

logger = logging.getLogger("ucoin")


class ConnectionHandler(object):
    """Helper class used by other API classes to ease passing server connection information."""

    def __init__(self, server, port):
        """
        Arguments:
        - `server`: server hostname
        - `port`: port number
        """

        self.server = server
        self.port = port
        self.connector = None

    def __str__(self):
        return 'connection info: %s:%d' % (self.server, self.port)


class API(object):
    """APIRequest is a class used as an interface. The intermediate derivated classes are the modules and the leaf classes are the API requests."""

    aiohttp_connector = None

    def __init__(self, connection_handler, module):
        """
        Asks a module in order to create the url used then by derivated classes.

        Arguments:
        - `module`: module name
        - `connection_handler`: connection handler
        """

        self.module = module
        self.connection_handler = connection_handler
        self.headers = {}

    def reverse_url(self, path):
        """
        Reverses the url using self.url and path given in parameter.

        Arguments:
        - `path`: the request path
        """

        server, port = self.connection_handler.server, self.connection_handler.port

        url = 'http://%s:%d/%s' % (server, port, self.module)
        return url + path

    def get(self, **kwargs):
        """wrapper of overloaded __get__ method."""

        return self.__get__(**kwargs)

    def post(self, **kwargs):
        """wrapper of overloaded __post__ method."""

        logger.debug('do some work with')

        data = self.__post__(**kwargs)

        logger.debug('and send back')

        return data

    def __get__(self, **kwargs):
        """interface purpose for GET request"""
        pass

    def __post__(self, **kwargs):
        """interface purpose for POST request"""
        pass

    @asyncio.coroutine
    def requests_get(self, path, **kwargs):
        """
        Requests GET wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """

        logging.debug("Request : {0}".format(self.reverse_url(path)))
        response = yield from asyncio.wait_for(aiohttp.get(self.reverse_url(path), params=kwargs,
                                headers=self.headers, connector=API.aiohttp_connector), timeout=30)

        if response.status != 200:
            raise ValueError('status code != 200 => %d (%s)' % (response.status, (yield from response.text())))

        return response

    def requests_post(self, path, **kwargs):
        """
        Requests POST wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """
        if 'self_' in kwargs:
            kwargs['self'] = kwargs.pop('self_')

        logging.debug("POST : {0}".format(kwargs))
        response = yield from asyncio.wait_for(
            aiohttp.post(self.reverse_url(path), data=kwargs, headers=self.headers,
                         connector=API.aiohttp_connector),
                                 timeout=30)
        return response

from . import network, blockchain, tx, wot, node, ud
