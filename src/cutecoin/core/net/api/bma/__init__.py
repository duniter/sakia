

__all__ = ['api']

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QUrlQuery, QTimer, QObject, pyqtSlot
import logging
import asyncio

logger = logging.getLogger("ucoin")

PROTOCOL_VERSION = "1"

@asyncio.coroutine
def timeout(reply, seconds):
    #logging.debug("Sleep timeout...")
    yield from asyncio.sleep(seconds)
    if reply.isRunning():
        #logging.debug("Reply aborted because of timeout")
        reply.abort()


class ConnectionHandler(object):
    """Helper class used by other API classes to ease passing server connection information."""

    def __init__(self, network_manager, server, port):
        """
        Arguments:
        - `server`: server hostname
        - `port`: port number
        """

        self.network_manager = network_manager
        self.server = server
        self.port = port

    def __str__(self):
        return 'connection info: %s:%d' % (self.server, self.port)


class API(object):
    """APIRequest is a class used as an interface. The intermediate derivated classes are the modules and the leaf classes are the API requests."""

    def __init__(self, conn_handler, module):
        """
        Asks a module in order to create the url used then by derivated classes.

        Arguments:
        - `module`: module name
        - `connection_handler`: connection handler
        """

        self.module = module
        self.conn_handler = conn_handler
        self.headers = {}

    def reverse_url(self, path):
        """
        Reverses the url using self.url and path given in parameter.

        Arguments:
        - `path`: the request path
        """

        server, port = self.conn_handler.server, self.conn_handler.port

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

    def requests_get(self, path, **kwargs):
        """
        Requests GET wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """
        query = QUrlQuery()
        for k,v in kwargs.items():
            query.addQueryItem(k, v);
        url = QUrl(self.reverse_url(path))
        url.setQuery(query)
        request = QNetworkRequest(url)
        logging.debug(url.toString())

        reply = self.conn_handler.network_manager.get(request)
        asyncio.async(timeout(reply, 15))

        return reply

    def requests_post(self, path, **kwargs):
        """
        Requests POST wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """
        if 'self_' in kwargs:
            kwargs['self'] = kwargs.pop('self_')

        logging.debug("POST : {0}".format(kwargs))
        post_data = QUrlQuery()
        for k, v in kwargs.items():
            if type(k) is str:
                k = k.replace("+", "%2b")
            if type(v) is str:
                v = v.replace("+", "%2b")
            else:
                v = json.dumps(v)
                v = v.replace("+", "%2b")
            post_data.addQueryItem(k, v)
        url = QUrl(self.reverse_url(path))
        url.setQuery(post_data)

        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader,
            "application/x-www-form-urlencoded")
        reply = self.conn_handler.network_manager.post(request,
                             post_data.toString(QUrl.FullyEncoded).encode('utf-8'))
        logging.debug(url.toString(QUrl.FullyEncoded))
        asyncio.async(timeout(reply, 15))
        return reply

from . import network, blockchain, tx, wot, ud, node
