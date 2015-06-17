from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtNetwork import QNetworkReply
from . import blockchain, network, node, tx, wot, ConnectionHandler
from .....tools.exceptions import NoPeerAvailable
import logging
import json
import random

class BmaAccess(QObject):
    '''
    This class is used to access BMA API.
    '''

    __saved_requests = [str(blockchain.Block), str(blockchain.Parameters)]

    def __init__(self, data, network):
        """
        Constructor of a network

        :param dict data: The data present in this cache
        :param cutecoin.core.net.network.Network network: The network used to connect
        """
        super().__init__()
        self._data = data
        self._network = network

    @classmethod
    def create(cls, network):
        '''
        Initialize a new BMAAccess object with empty data.

        :param cutecoin.core.net.network.Network network:
        :return: A new BmaAccess object
        :rtype: cutecoin.core.net.api.bma.access.BmaAccess
        '''
        return cls({}, network)

    @property
    def data(self):
        return self._data.copy()

    def load_from_json(self, json_data):
        '''
        Put data in the cache from json datas.

        :param dict data: The cache in json format
        '''
        data = {}
        for entry in json_data:
            key = entry['key']
            cache_key = (key[0], key[1], key[2], key[3], key[4])
            data[cache_key] = entry['value']
        self._data = data

    def jsonify(self):
        '''
        Get the cache in json format

        :return: The cache as a dict in json format
        '''
        data = {k: self._data[k] for k in self._data.keys()}
        entries = []
        for d in data:
            entries.append({'key': d,
                            'value': data[d]})
        return entries

    def get(self, caller, request, req_args={}, get_args={}):
        """
        Get Json data from the specified URL
        :rtype : dict
        """
        cache_key = (str(request),
                     str(tuple(frozenset(sorted(req_args.keys())))),
                     str(tuple(frozenset(sorted(req_args.values())))),
                     str(tuple(frozenset(sorted(get_args.keys())))),
                     str(tuple(frozenset(sorted(get_args.values())))))

        if cache_key in self._data.keys():
            need_reload = False
            if 'metadata' in self._data[cache_key]:
                if str(request) not in BmaAccess.__saved_requests \
                   and self._data[cache_key]['metadata']['block'] < self._network.latest_block:
                    need_reload = True
            else:
                need_reload = True
            ret_data = self._data[cache_key]['value']
        else:
            need_reload = True
            ret_data = request.null_value

        if need_reload:
            #Move to network nstead of community
            #after removing qthreads
            reply = self.request(request, req_args, get_args)
            reply.finished.connect(lambda:
                                     self.handle_reply(caller, request, req_args, get_args))
        return ret_data

    def request(self, request, req_args={}, get_args={}):
        '''
        Start a request to the network.

        :param request: A bma request class calling for data
        :param req_args: Arguments to pass to the request constructor
        :param get_args: Arguments to pass to the request __get__ method
        :return: The returned data if cached = True else return the QNetworkReply
        '''
        nodes = self._network.synced_nodes
        if len(nodes) > 0:
            node = random.choice(nodes)
            server = node.endpoint.conn_handler().server
            port = node.endpoint.conn_handler().port
            conn_handler = ConnectionHandler(self._network.network_manager, server, port)
            req = request(conn_handler, **req_args)
            reply = req.get(**get_args)
            return reply
        else:
            raise NoPeerAvailable(self.currency, len(nodes))

    @pyqtSlot(int, dict, dict, QObject)
    def handle_reply(self, caller, request, req_args, get_args):
        reply = self.sender()
        #logging.debug("Handling QtNetworkReply for {0}".format(str(request)))
        if reply.error() == QNetworkReply.NoError:
            cache_key = (str(request),
                         str(tuple(frozenset(sorted(req_args.keys())))),
                         str(tuple(frozenset(sorted(req_args.values())))),
                         str(tuple(frozenset(sorted(get_args.keys())))),
                         str(tuple(frozenset(sorted(get_args.values())))))
            strdata = bytes(reply.readAll()).decode('utf-8')
            #logging.debug("Data in reply : {0}".format(strdata))

            if cache_key not in self._data:
                self._data[cache_key] = {}

            if 'metadata' not in self._data[cache_key]:
                self._data[cache_key]['metadata'] = {}
            self._data[cache_key]['metadata']['block'] = self._network.latest_block

            change = False
            if 'value' in self._data[cache_key]:
                if self._data[cache_key]['value'] != json.loads(strdata):
                    change = True
            else:
                change = True

            if change == True:
                self._data[cache_key]['value'] = json.loads(strdata)
                caller.inner_data_changed.emit(request)
        else:
            logging.debug("Error in reply : {0}".format(reply.error()))
            self.community.qtrequest(caller, request, req_args, get_args)
