'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy import PROTOCOL_VERSION
from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from ucoinpy.documents.peer import Peer
from ucoinpy.documents.certification import SelfCertification, Certification
from ucoinpy.documents.membership import Membership
from ucoinpy.key import SigningKey
from ..tools.exceptions import PersonNotFoundError

import logging
import hashlib
import time

from .wallet import Wallet
from .community import Community
from .person import Person


class Account(object):

    '''
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    '''

    def __init__(self, salt, pubkey, name, communities, wallets, contacts):
        '''
        Constructor
        '''
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts

    @classmethod
    def create(cls, name, communities, wallets, confpath):
        '''
        Constructor
        '''
        account = cls(None, None, name, communities, wallets, [])
        return account

    @classmethod
    def load(cls, json_data):
        salt = json_data['salt']
        pubkey = json_data['pubkey']

        name = json_data['name']
        contacts = []

        for contact_data in json_data['contacts']:
            contacts.append(Person.from_json(contact_data))

        wallets = []
        for data in json_data['wallets']:
            wallets.append(Wallet.load(data))

        communities = []
        for data in json_data['communities']:
            communities.append(Community.load(data))

        account = cls(salt, pubkey, name, communities, wallets, contacts)
        return account

    def __eq__(self, other):
        if other is not None:
            return other.pubkey == self.pubkey
        else:
            return False

    def check_password(self, password):
        key = SigningKey(self.salt, password)
        return (key.pubkey == self.pubkey)

    def add_contact(self, person):
        self.contacts.append(person)

    def add_community(self, server, port):
        logging.debug("Adding a community")
        current = bma.blockchain.Current(ConnectionHandler(server, port))
        block_data = current.get()
        currency = block_data['currency']
        logging.debug("Currency : {0}".format(currency))

        peering = bma.network.Peering(ConnectionHandler(server, port))
        peer_data = peering.get()
        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                      peer_data['signature']))

        community = Community.create(currency, peer)
        self.communities.append(community)
        return community

    def set_walletpool_size(self, size, password):
        logging.debug("Defining wallet pool size")
        if len(self.wallets) < size:
            for i in range(len(self.wallets), size):
                wallet = Wallet.create(i, self.salt, password, "Wallet {0}".format(i))
                self.wallets.append(wallet)
        else:
            self.wallets = self.wallets[:size]

    def certify(self, password, community, pubkey):
        certified = Person.lookup(pubkey, community)
        block = community.get_block()
        block_hash = hashlib.sha1(block.signed_raw().encode("ascii")).hexdigest().upper()

        certification = Certification(PROTOCOL_VERSION, community.currency,
                                      self.pubkey, certified.pubkey,
                                      block_hash, block.number, None)

        selfcert = certified.selfcert(community)
        logging.debug("SelfCertification : {0}".format(selfcert.raw()))

        key = SigningKey(self.salt, password)
        certification.sign(selfcert, [key])
        signed_cert = certification.signed_raw(selfcert)
        logging.debug("Certification : {0}".format(signed_cert))

        data = {'pubkey': certified.pubkey,
                        'self_': selfcert.signed_raw(),
                        'other': "{0}\n".format(certification.inline())}
        logging.debug("Posted data : {0}".format(data))
        community.post(bma.wot.Add, {}, data)

    def sources(self, community):
        sources = []
        for w in self.wallets:
            for s in w.sources(community):
                sources.append(s)
        return sources

    def transactions_received(self, community):
        received = []
        for w in self.wallets:
            for t in w.transactions_received(community):
                received.append(t)
        return received

    def transactions_sent(self, community):
        sent = []
        for w in self.wallets:
            for t in w.transactions_sent(community):
                sent.append(t)
        return sent

    def member_of(self, community):
        pubkeys = community.members_pubkeys()
        if self.pubkey not in pubkeys:
            logging.debug("{0} not found in members : {1}".format(self.pubkey,
                                                                  pubkeys))
            return False
        return True

    def send_pubkey(self, password, community):
        selfcert = SelfCertification(PROTOCOL_VERSION,
                                     community.currency,
                                     self.pubkey,
                                     int(time.time()),
                                     self.name,
                                     None)
        key = SigningKey(self.salt, password)
        selfcert.sign([key])
        logging.debug("Key publish : {0}".format(selfcert.signed_raw()))
        community.post(bma.wot.Add, {}, {'pubkey': self.pubkey,
                                    'self_': selfcert.signed_raw(),
                                    'other': []})

    def send_membership(self, password, community, type):
        self_ = Person.lookup(self.pubkey, community)
        selfcert = self_.selfcert(community)

        block = community.get_block()
        block_hash = hashlib.sha1(block.signed_raw().encode("ascii")).hexdigest().upper()
        membership = Membership(PROTOCOL_VERSION, community.currency,
                          selfcert.pubkey, block.number,
                          block_hash, type, selfcert.uid,
                          selfcert.timestamp, None)
        key = SigningKey(self.salt, password)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        community.post(bma.blockchain.Membership, {},
                       {'membership': membership.signed_raw()})

    def jsonify(self):
        data_communities = []
        for c in self.communities:
            data_communities.append(c.jsonify())

        data_wallets = []
        for w in self.wallets:
            data_wallets.append(w.jsonify())

        data_contacts = []
        for p in self.contacts:
            data_contacts.append(p.jsonify())

        data = {'name': self.name,
                'salt': self.salt,
                'pubkey': self.pubkey,
                'communities': data_communities,
                'wallets': data_wallets,
                'contacts': data_contacts}
        return data
