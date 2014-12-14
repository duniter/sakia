'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.key import SigningKey
import logging
import json
import os
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.account.communities import Communities
from cutecoin.models.community import Community
from cutecoin.models.transaction import Transaction
from cutecoin.models.person import Person


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

        wallets = Wallets.load(json_data['wallets'])
        communities = Communities.load(json_data['communities'])

        account = cls(salt, pubkey, name, communities, wallets, contacts)
        return account

    def __eq__(self, other):
        if other is not None:
            return other.keyid == self.keyid
        else:
            return False

    def add_contact(self, person):
        self.contacts.append(person)

    def add_community(self, default_node):
        logging.debug("Adding a community")
        current = bma.blockchain.Current(default_node.connection_handler())
        block_data = current.get()
        currency = block_data['currency']
        logging.debug("Currency : {0}".format(currency))
        community = self.communities.add_community(currency, default_node)
        self.wallets.add_wallet(self.wallets.nextid(), currency)
        return community

    def transactions_received(self):
        received = []
        for w in self.wallets:
            for r in w.transactions_received():
                received.append(r)
        return received

    def transactions_sent(self):
        sent = []
        for w in self.wallets:
            for t in w.transactions_sent():
                sent.append(t)
        return sent

    def send_pubkey(self, community):
        return community.send_pubkey(self)

    def send_membership_in(self, community):
        return community.send_membership(self, "IN")

    def send_membership_out(self, community):
        return community.send_membership(self, "OUT")

    def jsonify_contacts(self):
        data = []
        for p in self.contacts:
            data.append(p.jsonify())
        return data

    def jsonify(self):
        data = {'name': self.name,
                'salt': self.salt,
                'pubkey': self.pubkey,
                'communities': self.communities.jsonify(),
                'wallets': self.wallets.jsonify(),
                'contacts': self.jsonify_contacts()}
        return data
