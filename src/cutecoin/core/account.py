'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from ucoinpy.documents.peer import Peer
import logging
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

        wallet = Wallet.create(self.next_walletid(), self.pubkey,
                               currency, "Default wallet")
        self.wallets.append(wallet)

        return community

    def next_walletid(self):
        wid = 0
        for w in self.wallets:
            if w.walletid > wid:
                wid = w.walletid + 1
        return wid

    def sources(self):
        #TODO: Change the way things are displayed
        # Listing sources from all communities is stupid
        received = []
        for c in self.communities:
            for w in self.wallets:
                for s in w.sources(c):
                    received.append(s)
        return received

    def transactions_sent(self):
        sent = []
        for w in self.wallets:
            for t in w.transactions_sent():
                sent.append(t)
        return sent

    def member_of(self, community):
        pubkeys = community.members_pubkeys()
        if self.pubkey not in pubkeys:
            logging.debug("{0} not found in members : {1}".format(self.pubkey,
                                                                  pubkeys))
            return False
        return True

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

    def jsonify_wallets(self):
        data = []
        for w in self.wallets:
            data.append(w.jsonify())
        return data

    def jsonify_community(self):
        data = []
        for c in self.communities:
            data.append(c.jsonify())
        return data

    def jsonify(self):
        data = {'name': self.name,
                'salt': self.salt,
                'pubkey': self.pubkey,
                'communities': self.jsonify_community(),
                'wallets': self.jsonify_wallets(),
                'contacts': self.jsonify_contacts()}
        return data
