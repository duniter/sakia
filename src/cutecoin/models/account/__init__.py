'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import gnupg
import logging
import json
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.account.communities import Communities
from cutecoin.models.community import Community
from cutecoin.models.transaction import Transaction
from cutecoin.models.person import Person
from cutecoin.core.exceptions import CommunityNotFoundError


class Account(object):

    '''
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    '''

    def __init__(self, keyid, name, communities, wallets, contacts):
        '''
        Constructor
        '''
        self.keyid = keyid
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts

    @classmethod
    def create(cls, keyid, name, communities):
        '''
        Constructor
        '''
        wallets = Wallets()
        account = cls(keyid, name, communities, wallets, [])
        for community in account.communities.communities_list:
            wallet = account.wallets.add_wallet(community)
            wallet.refresh_coins(account.fingerprint())
        return account

    @classmethod
    def load(cls, json_data):
        keyid = json_data['keyid']
        name = json_data['name']
        communities = Communities()
        wallets = Wallets()
        contacts = []

        for contact_data in json_data['contacts']:
            contacts.append(Person.from_json(contact_data))

        account = cls(keyid, name, communities, wallets, contacts)

        for community_data in json_data['communities']:
            account.communities.communities_list.append(
                Community.load(
                    community_data,
                    account))

        return account

    def __eq__(self, other):
        if other is not None:
            return other.keyid == self.keyid
        else:
            return False

    def add_contact(self, person):
        self.contacts.append(person)

    def fingerprint(self):
        gpg = gnupg.GPG()
        available_keys = gpg.list_keys()
        logging.debug(self.keyid)
        for k in available_keys:
            logging.debug(k)
            if k['keyid'] == self.keyid:
                return k['fingerprint']
        return ""

    def transactions_received(self):
        received = []
        for community in self.communities.communities_list:
            transactions_data = community.network.request(
                ucoin.hdc.transactions.Recipient(
                    self.fingerprint()))
            for trx_data in transactions_data:
                received.append(
                    Transaction.create(
                        trx_data['value']['transaction']['sender'],
                        trx_data['value']['transaction']['number'],
                        community))
        return received

    def transactions_sent(self):
        sent = []
        for community in self.communities.communities_list:
            transactions_data = community.network.request(
                ucoin.hdc.transactions.sender.Last(
                    self.fingerprint(),
                    20))
            for trx_data in transactions_data:
                # Small bug in ucoinpy library
                if not isinstance(trx_data, str):
                    sent.append(
                        Transaction.create(
                            trx_data['value']['transaction']['sender'],
                            trx_data['value']['transaction']['number'],
                            community))
        return sent

    def transfer_coins(self, node, recipient, coins, message):
        transfer = ucoin.wrappers.transactions.RawTransfer(
            self.fingerprint(),
            recipient.fingerprint,
            coins,
            message,
            keyid=self.keyid,
            server=node.server,
            port=node.port)
        return transfer()

    #TODO: Adapt to new WHT
    def tht(self, community):
        if community in self.communities.communities_list:
            #tht = community.ucoinRequest(ucoin.wallets.tht(self.fingerprint()))
            #return tht['entries']
            return None
        return None

    def push_tht(self, community):
        if community in self.communities.communities_list:
            hosters_fg = []
            trusts_fg = []
            for trust in community.network.trusts():
                peering = trust.peering()
                logging.debug(peering)
                trusts_fg.append(peering['fingerprint'])
            for hoster in community.network.hosters():
                logging.debug(peering)
                peering = hoster.peering()
                hosters_fg.append(peering['fingerprint'])
            entry = {
                'version': '1',
                'currency': community.currency,
                'fingerprint': self.fingerprint(),
                'hosters': hosters_fg,
                'trusts': trusts_fg
            }
            logging.debug(entry)
            json_entry = json.JSONEncoder(indent=2).encode(entry)
            gpg = gnupg.GPG()
            signature = gpg.sign(json_entry, keyid=self.keyid, clearsign=True)

            dataPost = {
                'entry': entry,
                'signature': str(signature)
            }

            #community.network.post(
            #    ucoin.ucg.THT(
            #        pgp_fingerprint=self.fingerprint()),
            #    dataPost)
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def pull_tht(self, community):
        if community in self.communities.communities_list:
            community.pull_tht(self.fingerprint())
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def quality(self, community):
        if community in self.communities.communities_list:
            return community.person_quality(self.fingerprint())
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def jsonify_contacts(self):
        data = []
        for p in self.contacts:
            data.append(p.jsonify())
        return data

    def jsonify(self):
        data = {'name': self.name,
                'keyid': self.keyid,
                'communities': self.communities.jsonify(self.wallets),
                'contacts': self.jsonify_contacts()}
        return data
