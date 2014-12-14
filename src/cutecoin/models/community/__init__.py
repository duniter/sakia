'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
import hashlib
import json
import logging
import time
from cutecoin.models.node import Node
from cutecoin.models.account.wallets import Wallets


class Community(object):
    '''
    classdocs
    '''
    def __init__(self, currency, nodes):
        '''
        A community is a group of nodes using the same currency.
        '''
        self.currency = currency
        self.nodes = nodes

    @classmethod
    def create(cls, currency, default_node):
        return cls(currency, [default_node])

    @classmethod
    def load(cls, json_data):
        nodes = []

        for node_data in json_data['nodes']:
            nodes.append(Node.load(node_data))

        currency = json_data['currency']

        community = cls(currency, nodes)
        return community

    def name(self):
        return self.currency

    def __eq__(self, other):
        return (other.currency == self.currency)

    def dividend(self):
        current_amendment = self.request(bma.blockchain.Current())
        return int(current_amendment['du'])

    def send_pubkey(self, account):
        pass

    def send_membership(self, account, membership):
        pass

    def members_pubkeys(self, wallets):
        '''
        Listing members of a community
        '''
        memberships = self.request(bma.wot.Members())
        members = []
        for m in memberships:
            members.append(m['results']['pubkey'])
        return members

    def request(self, request, get_args={}):
        for node in self.nodes():
            logging.debug("Trying to connect to : " + node.get_text())
            request.connection_handler = node.connection_handler()
            try:
                data = request.get(**get_args)
                return data
            except:
                continue
        return None

    def post(self, request, get_args={}):
        error = None
        for node in self.nodes():
            logging.debug("Trying to connect to : " + node.get_text())
            request.connection_handler = node.connection_handler()
            try:
                request.post(**get_args)
            except ValueError as e:
                error = str(e)
            except:
                continue
        return error

    def broadcast(self, nodes, request, get_args={}):
        error = None
        for node in nodes:
            logging.debug("Trying to connect to : " + node.get_text())
            request.connection_handler = node.connection_handler()
            try:
                request.post(**get_args)
            except ValueError as e:
                error = str(e)
            except:
                continue
        return error

    def jsonify(self):
        data = {'currency': self.currency}
        return data
