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
        same_contact = [contact for contact in self.contacts if person.pubkey == contact.pubkey]
        if len(same_contact) == 0:
            print("add contact")
            self.contacts.append(person)
            return True
        return False

    def add_community(self, server, port):
        logging.debug("Adding a community")

        peering = bma.network.Peering(ConnectionHandler(server, port))
        peer_data = peering.get()
        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                      peer_data['signature']))
        currency = peer.currency

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

        try:
            block = community.get_block()
            block_number = block.number
            block_hash = hashlib.sha1(block.signed_raw().encode("ascii")).hexdigest().upper()
        except ValueError as e:
            block_number = 0
            block_hash = "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"

        certification = Certification(PROTOCOL_VERSION, community.currency,
                                      self.pubkey, certified.pubkey,
                                      block_hash, block_number, None)

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
        community.broadcast(bma.wot.Add, {}, data)

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
                # Lets remove transactions from our own wallets
                pubkeys = [wallet.pubkey for wallet in self.wallets]
                if t.issuers[0] not in pubkeys:
                    received.append(t)
        return received

    def transactions_sent(self, community):
        sent = []
        for w in self.wallets:
            for t in w.transactions_sent(community):
                # Lets remove transactions to our own wallets
                pubkeys = [wallet.pubkey for wallet in self.wallets]
                outputs = [o for o in t.outputs if o.pubkey not in pubkeys]
                if len(outputs) > 0:
                    sent.append(t)
        return sent

    def transactions_awaiting(self, community):
        awaiting = []
        for w in self.wallets:
            for t in w.transactions_awaiting(community):
                # Lets remove transactions to our own wallets
                pubkeys = [wallet.pubkey for wallet in self.wallets]
                outputs = [o for o in t.outputs if o.pubkey not in pubkeys]
                if len(outputs) > 0:
                    awaiting.append(t)
        return awaiting

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
        community.broadcast(bma.wot.Add, {}, {'pubkey': self.pubkey,
                                    'self_': selfcert.signed_raw(),
                                    'other': []})

    def send_membership(self, password, community, type):
        self_ = Person.lookup(self.pubkey, community)
        selfcert = self_.selfcert(community)

        try:
            block = community.get_block()
            block_hash = hashlib.sha1(block.signed_raw().encode("ascii")).hexdigest().upper()
            block_number = block.number
        except ValueError as e:
            block_number = 0
            block_hash = "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"

        membership = Membership(PROTOCOL_VERSION, community.currency,
                          selfcert.pubkey, block_number,
                          block_hash, type, selfcert.uid,
                          selfcert.timestamp, None)
        key = SigningKey(self.salt, password)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        community.broadcast(bma.blockchain.Membership, {},
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
