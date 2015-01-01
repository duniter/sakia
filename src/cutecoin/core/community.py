'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy import PROTOCOL_VERSION
from ucoinpy.documents.peer import Peer, Endpoint, BMAEndpoint
from ucoinpy.documents.block import Block
import logging
import time
import inspect


class Community(object):
    '''
    classdocs
    '''
    def __init__(self, currency, peers):
        '''
        A community is a group of nodes using the same currency.
        '''
        self.currency = currency
        self.peers = peers
        self.requests_cache = {}
        self.last_block = None

        # After initializing the community from latest peers,
        # we refresh its peers tree
        found_peers = self.peering()
        for p in found_peers:
            if p.pubkey not in [peer.pubkey for peer in peers]:
                self.peers.append(p)

    @classmethod
    def create(cls, currency, peer):
        return cls(currency, [peer])

    @classmethod
    def load(cls, json_data):
        peers = []

        currency = json_data['currency']

        for data in json_data['peers']:
            endpoint_inline = next(e for e in data['endpoints']
                            if Endpoint.from_inline(e) is not None)
            endpoint = Endpoint.from_inline(endpoint_inline)
            try:
                peering = bma.network.Peering(endpoint.conn_handler())
                peer_data = peering.get()
                peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))
                peers.append(peer)
            except:
                pass

        community = cls(currency, peers)
        return community

    def name(self):
        return self.currency

    def __eq__(self, other):
        return (other.currency == self.currency)

    def dividend(self):
        ud = self.request(bma.blockchain.UD)
        block_number = ud['result']['blocks'][-1]
        block = self.request(bma.blockchain.Block,
                             req_args={'number': block_number})
        return block['dividend']

    def peering(self):
        peers = []
        peering_data = self.request(bma.network.peering.Peers)
        logging.debug("Peering : {0}".format(peering_data))
        for peer in peering_data:
            logging.debug(peer)
            peers.append(Peer.from_signed_raw("{0}{1}\n".format(peer['value']['raw'],
                                                                peer['value']['signature'])))
        return peers

    def get_block(self, number=None):
        if number is None:
            data = self.request(bma.blockchain.Current)
        else:
            data = self.request(bma.blockchain.Block,
                                req_args={'number': number})

        return Block.from_signed_raw("{0}{1}\n".format(data['raw'],
                                                       data['signature']))

    def members_pubkeys(self):
        '''
        Listing members pubkeys of a community
        '''
        memberships = self.request(bma.wot.Members)
        members = []
        logging.debug(memberships)
        for m in memberships["results"]:
            members.append(m['pubkey'])
        return members

    def request(self, request, req_args={}, get_args={}):
        for peer in self.peers:
            e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
            # We request the current block every five minutes
            # If a new block is mined we reset the cache
            if self.last_block is None:
                block = bma.blockchain.Current(e.conn_handler()).get()
                self.last_block = {"request_ts": time.time(),
                                   "number": block['number']}
            elif self.last_block["request_ts"] < time.time() - 300:
                block = bma.blockchain.Current(e.conn_handler()).get()
                if block['number'] > self.last_block['number']:
                    self.last_block = {"request_ts": time.time(),
                                       "number": block['number']}
                    self.requests_cache = {}

            cache_key = (hash(request),
                         hash(tuple(frozenset(sorted(req_args.keys())))),
                         hash(tuple(frozenset(sorted(req_args.items())))),
                         hash(tuple(frozenset(sorted(get_args.keys())))),
                         hash(tuple(frozenset(sorted(get_args.items())))))

            if cache_key not in self.requests_cache.keys():
                logging.debug("Connecting to {0}:{1}".format(e.server,
                                                             e.port))
                req = request(e.conn_handler(), **req_args)
                data = req.get(**get_args)
                if inspect.isgenerator(data):
                    cached_data = []
                    for d in data:
                        cached_data.append(d)
                    self.requests_cache[cache_key] = cached_data
                    logging.debug("Got a generator !")
                else:
                    self.requests_cache[cache_key] = data
            return self.requests_cache[cache_key]

    def post(self, request, req_args={}, post_args={}):
        for peer in self.peers:
            e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
            logging.debug("Trying to connect to : " + peer.pubkey)
            req = request(e.conn_handler(), **req_args)
            try:
                req.post(**post_args)
            except ValueError as e:
                raise
            except:
                pass
            return

    def jsonify_peers_list(self):
        data = []
        for peer in self.peers:
            endpoints_data = []
            for e in peer.endpoints:
                endpoints_data.append(e.inline())
            data.append({'endpoints': endpoints_data,
                         'pubkey': peer.pubkey})
        return data

    def jsonify(self):
        data = {'currency': self.currency,
                'peers': self.jsonify_peers_list()}
        return data

    def get_parameters(self):
        return self.request(bma.blockchain.Parameters)
