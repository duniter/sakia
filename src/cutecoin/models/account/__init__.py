'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import gnupg
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

    def __init__(self, keyid, name, communities, wallets, contacts,
                 keyring, secret_keyring):
        '''
        Constructor
        '''
        self.keyid = keyid
        self.name = name
        self.communities = communities
        print(len(communities))
        self.wallets = wallets
        self.contacts = contacts
        self.keyring = keyring
        self.secret_keyring = secret_keyring
        self.gpg = gnupg.GPG(keyring=self.keyring,
                    secret_keyring=self.secret_keyring)

    @classmethod
    def create(cls, name, communities, wallets, confpath):
        '''
        Constructor
        '''
        keyring = os.path.join(confpath['home'], name, "keyring")
        secret_keyring = os.path.join(confpath['home'], name, "secretkeyring")
        account = cls('', name, communities, wallets, [],
                      keyring, secret_keyring)
        return account

    @classmethod
    def load(cls, json_data):
        keyid = json_data['keyid']
        name = json_data['name']
        keyring = json_data['keyring']
        secret_keyring = json_data['secret_keyring']
        contacts = []

        for contact_data in json_data['contacts']:
            contacts.append(Person.from_json(contact_data))

        wallets = Wallets.load(json_data['wallets'])
        communities = Communities.load(json_data['communities'])

        account = cls(keyid, name, communities, wallets, contacts,
                      keyring, secret_keyring)
        return account

    def __eq__(self, other):
        if other is not None:
            return other.keyid == self.keyid
        else:
            return False

    def add_contact(self, person):
        self.contacts.append(person)

    def add_community(self, default_node):
        promoted = ucoin.hdc.amendments.Promoted()
        default_node.use(promoted)
        amendment_data = promoted.get()
        currency = amendment_data['currency']
        community = self.communities.add_community(currency)
        self.wallets.add_wallet(self.gpg,
                                self.keyid,
                                   currency,
                                   default_node)
        return community

    def fingerprint(self):
        available_keys = self.gpg.list_keys()
        logging.debug(self.keyid)
        for k in available_keys:
            logging.debug(k)
            if k['keyid'] == self.keyid:
                return k['fingerprint']
        return ""

    def transactions_received(self):
        received = []
        for w in self.wallets:
            for r in w.transactions_received(self.gpg):
                received.append(r)
        return received

    def transactions_sent(self):
        sent = []
        for w in self.wallets:
            for t in w.transactions_sent(self.gpg):
                sent.append(t)
        return sent

    def send_pubkey(self, community):
        wallets = self.wallets.community_wallets(community.currency)
        return community.send_pubkey(self, wallets)

    def send_membership_in(self, community):
        wallets = self.wallets.community_wallets(community.currency)
        return community.send_membership(self, wallets, "IN")

    def send_membership_out(self, community):
        wallets = self.wallets.community_wallets(community.currency)
        return community.send_membership(self, wallets, "OUT")

    def quality(self, community):
        wallets = self.wallets.community_wallets(community.currency)
        return community.person_quality(wallets, self.fingerprint())

    def jsonify_contacts(self):
        data = []
        for p in self.contacts:
            data.append(p.jsonify())
        return data

    def jsonify(self):
        data = {'name': self.name,
                'keyid': self.keyid,
                'communities': self.communities.jsonify(),
                'wallets': self.wallets.jsonify(),
                'contacts': self.jsonify_contacts(),
                'keyring': self.keyring,
                'secret_keyring': self.secret_keyring}
        return data
