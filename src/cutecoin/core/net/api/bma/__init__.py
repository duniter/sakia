__all__ = ['api']

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtCore import QUrl, QUrlQuery
import logging, json
# import pylibscrypt

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

    def __str__(self):
        return 'connection info: %s:%d' % (self.server, self.port)


class API(object):
    """APIRequest is a class used as an interface. The intermediate derivated classes are the modules and the leaf classes are the API requests."""

    def __init__(self, network_manager, connection_handler, module):
        """
        Asks a module in order to create the url used then by derivated classes.

        Arguments:
        - `module`: module name
        - `connection_handler`: connection handler
        """

        self.module = module
        self.network_manager = network_manager
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

    def requests_get(self, path, **kwargs):
        """
        Requests GET wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """
        url = QUrlQuery(self.reverse_url(path))
        for k,v in kwargs.items():
            url.addQueryItem(k, v);
        request = QNetworkRequest(url)
        reply = request.get(self.reverse_url(path), params=kwargs,
                                headers=self.headers, timeout=15)

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
        for k,v in kwargs.items():
            post_data.addQueryItem(k, v);

        request = QNetworkRequest(self.reverse_url(path))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
            "application/x-www-form-urlencoded");
        reply = request.post(self.reverse_url(path),
                             post_data.toString(QUrl.FullyEncoded).toUtf8())

        return reply

from . import network, blockchain, tx, wot
