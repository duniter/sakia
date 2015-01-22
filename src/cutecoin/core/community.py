'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy import PROTOCOL_VERSION
from ucoinpy.documents.peer import Peer, Endpoint, BMAEndpoint
from ucoinpy.documents.block import Block
from ..tools.exceptions import NoPeerAvailable
import logging
import inspect
import hashlib
from requests.exceptions import ConnectTimeout


class Cache():
    def __init__(self, community):
        self.latest_block = 0
        self.community = community
        self.data = {}

    def refresh(self):
        self.latest_block = self.community.current_blockid()['number']
        self.data = {}

    def request(self, request, req_args={}, get_args={}):
        cache_key = (hash(request),
                     hash(tuple(frozenset(sorted(req_args.keys())))),
                     hash(tuple(frozenset(sorted(req_args.items())))),
                     hash(tuple(frozenset(sorted(get_args.keys())))),
                     hash(tuple(frozenset(sorted(get_args.items())))))

        if cache_key not in self.data.keys():
            result = self.community.request(request, req_args, get_args,
                                         cached=False)

            # Do not cache block 0
            if self.latest_block == 0:
                return result
            else:
                self.data[cache_key] = result
            return self.data[cache_key]
        else:
            return self.data[cache_key]


class Community(object):
    '''
    classdocs
    '''

    def __init__(self, currency, peers):
        '''
        A community is a group of nodes using the same currency.
        '''
        self.currency = currency
        self.peers = [p for p in peers if p.currency == currency]
        self._cache = Cache(self)

        # After initializing the community from latest peers,
        # we refresh its peers tree
        logging.debug("Creating community")
        try:
            found_peers = self.peering()
            for p in found_peers:
                if p.pubkey not in [peer.pubkey for peer in peers]:
                    self.peers.append(p)
        except NoPeerAvailable:
            pass
        logging.debug("{0} peers found".format(len(self.peers)))

        try:
            self._cache.refresh()
        except NoPeerAvailable:
            pass

    @classmethod
    def create(cls, currency, peer):
        return cls(currency, [peer])

    @classmethod
    def load(cls, json_data):
        peers = []

        currency = json_data['currency']

        for data in json_data['peers']:
            for e in data['endpoints']:
                if Endpoint.from_inline(e) is not None:
                    endpoint = Endpoint.from_inline(e)
                    try:
                        peering = bma.network.Peering(endpoint.conn_handler())
                        peer_data = peering.get()
                        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                          peer_data['signature']))
                        peers.append(peer)
                        break
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
        if len(ud['result']['blocks']) > 0:
            block_number = ud['result']['blocks'][-1]
            block = self.request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block['dividend']
        else:
            return 1

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

    def current_blockid(self):
        try:
            block = self.request(bma.blockchain.Current, cached=False)
            signed_raw = "{0}{1}\n".format(block['raw'], block['signature'])
            block_hash = hashlib.sha1(signed_raw.encode("ascii")).hexdigest().upper()
            block_number = block['number']
        except ValueError as e:
            if '404' in str(e):
                block_number = 0
                block_hash = "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
            else:
                raise
        return {'number': block_number, 'hash': block_hash}

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

    def refresh_cache(self):
        self._cache.refresh()

    def request(self, request, req_args={}, get_args={}, cached=True):
        if cached:
            return self._cache.request(request, req_args, get_args)
        else:
            for peer in self.peers.copy():
                e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
                try:
                    req = request(e.conn_handler(), **req_args)
                    data = req.get(**get_args)

                    if inspect.isgenerator(data):
                        generated = []
                        for d in data:
                            generated.append(d)
                        return generated
                    else:
                        return data
                except ValueError as e:
                    if '502' in str(e):
                        continue
                    else:
                        raise
                except ConnectTimeout:
                    # Move the timeout peer to the end
                    self.peers.remove(peer)
                    self.peers.append(peer)
                    continue
                except TimeoutError:
                    # Move the timeout peer to the end
                    self.peers.remove(peer)
                    self.peers.append(peer)
                    continue

        raise NoPeerAvailable(self.currency, len(self.peers))

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
        raise NoPeerAvailable(self.currency, len(self.peers))

    def broadcast(self, request, req_args={}, post_args={}):
        for peer in self.peers:
            e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
            logging.debug("Trying to connect to : " + peer.pubkey)
            req = request(e.conn_handler(), **req_args)
            try:
                req.post(**post_args)
            except ValueError as e:
                if peer == self.peers[0]:
                    raise
            except:
                pass
        raise NoPeerAvailable(self.currency, len(self.peers))

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
