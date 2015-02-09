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
import re
from requests.exceptions import RequestException, Timeout


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

        self._cache.refresh()

    @classmethod
    def create(cls, currency, peer):
        community = cls(currency, [peer])
        logging.debug("Creating community")
        community.peers = community.peering()
        logging.debug("{0} peers found".format(len(community.peers)))
        logging.debug([peer.pubkey for peer in community.peers])
        return community

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
        logging.debug("Creating community")
        community.peers = community.peering()
        logging.debug("{0} peers found".format(len(community.peers)))
        logging.debug([peer.pubkey for peer in community.peers])
        return community

    @classmethod
    def without_network(cls, json_data):
        peers = []

        currency = json_data['currency']

        for data in json_data['peers']:
            endpoints = []
            for e in data['endpoints']:
                endpoints.append(Endpoint.from_inline(e))
            peer = Peer(PROTOCOL_VERSION, currency, data['pubkey'],
                        "0-DA39A3EE5E6B4B0D3255BFEF95601890AFD80709",
                        endpoints, None)
            peers.append(peer)

        community = cls(currency, peers)
        return community

    def name(self):
        return self.currency

    def __eq__(self, other):
        return (other.currency == self.currency)

    @property
    def short_currency(self):
        words = re.split('[_\W]+', self.currency)
        shortened = ""
        if len(words) > 1:
            shortened = ''.join([w[0] for w in words])
        else:
            vowels = ('a', 'e', 'i', 'o', 'u', 'y')
            shortened = self.currency
            shortened = ''.join([c for c in shortened if c not in vowels])
        return shortened

    @property
    def currency_symbol(self):
        letter = self.currency[0]
        u = ord('\u24B6') + ord(letter) - ord('A')
        return chr(u)

    @property
    def dividend(self):
        block = self.get_ud_block()
        if block:
            return block['dividend']
        else:
            return 1

    def get_ud_block(self):
        ud = self.request(bma.blockchain.UD)
        if len(ud['result']['blocks']) > 0:
            block_number = ud['result']['blocks'][-1]
            block = self.request(bma.blockchain.Block,
                                 req_args={'number': block_number})
            return block
        else:
            return False

    @property
    def monetary_mass(self):
        try:
            block = self.request(bma.blockchain.Current)
            return block['monetaryMass']
        except ValueError as e:
            if '404' in e:
                return 0

    @property
    def nb_members(self):
        try:
            block = self.request(bma.blockchain.Current)
            return block['membersCount']
        except ValueError as e:
            if '404' in e:
                return 0

    def _peering_traversal(self, peer, found_peers, traversed_pubkeys):
        logging.debug("Read {0} peering".format(peer.pubkey))
        traversed_pubkeys.append(peer.pubkey)
        if peer.currency == self.currency and \
            peer.pubkey not in [p.pubkey for p in found_peers]:
            found_peers.append(peer)
        try:
            e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
            next_peers = bma.network.peering.Peers(e.conn_handler()).get()
            for p in next_peers:
                next_peer = Peer.from_signed_raw("{0}{1}\n".format(p['value']['raw'],
                                                            p['value']['signature']))
                logging.debug(traversed_pubkeys)
                logging.debug("Traversing : next to read : {0} : {1}".format(next_peer.pubkey,
                              (next_peer.pubkey not in traversed_pubkeys)))
                if next_peer.pubkey not in traversed_pubkeys:
                    self._peering_traversal(next_peer, found_peers, traversed_pubkeys)
        except Timeout:
            pass
        except ConnectionError:
            pass
        except ValueError:
            pass
        except RequestException as e:
            pass

    def peering(self):
        peers = []
        traversed_pubkeys = []
        for p in self.peers:
            logging.debug(traversed_pubkeys)
            logging.debug("Peering : next to read : {0} : {1}".format(p.pubkey,
                          (p.pubkey not in traversed_pubkeys)))
            if p.pubkey not in traversed_pubkeys:
                self._peering_traversal(p, peers, traversed_pubkeys)

        logging.debug("Peers found : {0}".format(peers))
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
        return [m['pubkey'] for m in memberships["results"]]

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
                except RequestException:
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
                return
            except ValueError as e:
                raise
            except RequestException:
                # Move the timeout peer to the end
                self.peers.remove(peer)
                self.peers.append(peer)
                continue
            except:
                raise
        raise NoPeerAvailable(self.currency, len(self.peers))

    def broadcast(self, request, req_args={}, post_args={}):
        tries = 0
        ok = False
        value_error = None
        for peer in self.peers:
            e = next(e for e in peer.endpoints if type(e) is BMAEndpoint)
            logging.debug("Trying to connect to : " + peer.pubkey)
            req = request(e.conn_handler(), **req_args)
            try:
                req.post(**post_args)
                ok = True
            except ValueError as e:
                value_error = e
                continue
            except RequestException:
                tries = tries + 1
                # Move the timeout peer to the end
                self.peers.remove(peer)
                self.peers.append(peer)
                continue
            except:
                raise

        if not ok:
            raise value_error

        if tries == len(self.peers):
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
