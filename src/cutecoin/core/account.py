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

import logging
import time

from .wallet import Wallet
from .community import Community
from .person import Person
from ..tools.exceptions import NoPeerAvailable, ContactAlreadyExists


def quantitative(units, community):
    return int(units)


def relative(units, community):
    ud = community.dividend
    relative_value = units / float(ud)
    return relative_value


def quantitative_zerosum(units, community):
    median = community.monetary_mass / community.nb_members
    return units - median


def relative_zerosum(units, community):
    median = community.monetary_mass / community.nb_members
    ud = community.dividend
    relative_value = units / float(ud)
    relative_median = median / ud
    return relative_value - relative_median


class Account(object):

    '''
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    '''
    referentials = {'Units': (quantitative, '{0}', quantitative, '{0}'),
                    'UD': (relative, 'ud {0}', relative, 'ud {0}'),
                    'Quant Z-sum': (quantitative_zerosum, 'q0 {0}',
                                    quantitative, '{0}'),
                    'Relat Z-sum': (relative_zerosum, 'r0 {0}',
                                    relative, 'ud {0}')
                    }

    def __init__(self, salt, pubkey, name, communities, wallets, contacts,
                 dead_communities):
        '''
        Constructor
        '''
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.dead_communities = dead_communities
        self.wallets = wallets
        self.contacts = contacts
        self.referential = 'Units'

    @classmethod
    def create(cls, name, communities, wallets, confpath):
        '''
        Constructor
        '''
        account = cls(None, None, name, communities, wallets, [], [])
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
        dead_communities = []
        for data in json_data['communities']:
            try:
                community = Community.load(data)
                communities.append(community)
            except NoPeerAvailable:
                community = Community.without_network(data)
                dead_communities.append(community)

        account = cls(salt, pubkey, name, communities, wallets,
                      contacts, dead_communities)
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
        same_contact = [contact for contact in self.contacts
                        if person.pubkey == contact.pubkey]

        if len(same_contact) > 0:
            raise ContactAlreadyExists(person.uid, same_contact[0].uid)
        self.contacts.append(person)

    def add_community(self, community):
        logging.debug("Adding a community")
        self.communities.append(community)
        return community

    def refresh_cache(self):
        for w in self.wallets:
            for c in self.communities:
                w.refresh_cache(c)

    def set_display_referential(self, index):
        self.referential = index

    @property
    def units_to_ref(self):
        return Account.referentials[self.referential][0]

    @property
    def units_to_diff_ref(self):
        return Account.referentials[self.referential][2]

    def ref_name(self, currency):
        return Account.referentials[self.referential][1].format(currency)

    def diff_ref_name(self, currency):
        return Account.referentials[self.referential][3].format(currency)

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
        blockid = community.current_blockid()

        certification = Certification(PROTOCOL_VERSION, community.currency,
                                      self.pubkey, certified.pubkey,
                                      blockid['number'], blockid['hash'], None)

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

    def transfers(self, community):
        sent = []
        for w in self.wallets:
            for transfer in w.transfers(community):
                sent.append(transfer)
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
        community.broadcast(bma.wot.Add, {}, {'pubkey': self.pubkey,
                                    'self_': selfcert.signed_raw(),
                                    'other': []})

    def send_membership(self, password, community, type):
        self_ = Person.lookup(self.pubkey, community)
        selfcert = self_.selfcert(community)

        blockid = community.current_blockid()

        membership = Membership(PROTOCOL_VERSION, community.currency,
                          selfcert.pubkey, blockid['number'],
                          blockid['hash'], type, selfcert.uid,
                          selfcert.timestamp, None)
        key = SigningKey(self.salt, password)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        community.broadcast(bma.blockchain.Membership, {},
                       {'membership': membership.signed_raw()})

    def jsonify(self):
        data_communities = []
        communities = self.communities + self.dead_communities
        for c in communities:
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

    def get_person(self):
        return Person(self.name, self.pubkey)
