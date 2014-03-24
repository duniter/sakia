'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import gnupg
import logging
import json
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.account.communities import Communities
from cutecoin.models.community import Community
from cutecoin.models.transaction import factory
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
            wallet = account.wallets.add_wallet(community.currency)
            wallet.refresh_coins(community, account.key_fingerprint())
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

    def add_wallet(self, name, currency):
        self.wallets.add_wallet(name, currency)

    def add_contact(self, person):
        self.contacts.append(person)

    def key_fingerprint(self):
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
            transactions_data = community.ucoin_request(
                ucoin.hdc.transactions.Recipient(
                    self.key_fingerprint()))
            for trxData in transactions_data:
                received.append(
                    factory.create_transaction(
                        trxData['value']['transaction']['sender'],
                        trxData['value']['transaction']['number'],
                        community))
        return received

    def transactions_sent(self):
        sent = []
        for community in self.communities.communities_list:
            transactions_data = community.ucoin_request(
                ucoin.hdc.transactions.sender.Last(
                    self.key_fingerprint(),
                    20))
            for trx_data in transactions_data:
                # Small bug in ucoinpy library
                if not isinstance(trx_data, str):
                    sent.append(
                        factory.create_transaction(
                            trxData['value']['transaction']['sender'],
                            trxData['value']['transaction']['number'],
                            community))
        return sent

    def last_issuances(self, community):
        issuances = []
        if community in self.communities.communities_list:
            issuances_data = community.ucoin_request(
                ucoin.hdc.transactions.sender.Issuance(
                    self.key_fingerprint()))
            for issuance in issuances_data:
                logging.debug(issuance)
                issuances.append(
                    factory.create_transaction(
                        issuance['value']['transaction']['sender'],
                        issuance['value']['transaction']['number'],
                        community))
        return issuances

    def issued_last_dividend(self, community):
        current_amendment_number = community.amendment_number()
        if community in self.communities.communities_list:
            dividends_data = community.ucoin_request(
                ucoin.hdc.transactions.sender.issuance.Dividend(
                    self.key_fingerprint(),
                    current_amendment_number))
            for dividend in dividends_data:
                # Small bug in ucoinpy library
                if not isinstance(dividend, str):
                    return True
        return False

    def issue_dividend(self, community, coins):
        if community in self.communities.communities_list:
            logging.debug(coins)
            issuance = ucoin.wrappers.transactions.Issue(
                self.key_fingerprint(),
                community.amendment_number(),
                coins,
                keyid=self.keyid)
            return issuance()

    def tht(self, community):
        if community in self.communities.communities_list:
            tht = community.ucoinRequest(ucoin.ucg.tht(self.key_fingerprint()))
            return tht['entries']
        return None

    def push_tht(self, community):
        if community in self.communities.communities_list:
            hosters_fg = []
            trusts_fg = []
            for trust in community.trusts():
                peering = trust.peering()
                logging.debug(peering)
                trusts_fg.append(peering['fingerprint'])
            for hoster in community.hosters():
                logging.debug(peering)
                peering = hoster.peering()
                hosters_fg.append(peering['fingerprint'])
            entry = {
                'version': '1',
                'currency': community.currency,
                'fingerprint': self.key_fingerprint(),
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

            community.ucoin_post(
                ucoin.ucg.THT(
                    pgp_fingerprint=self.key_fingerprint()),
                dataPost)
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def pull_tht(self, community):
        if community in self.communities.communities_list:
            community.pull_tht(self.key_fingerprint())

    def transfer_coins(self, node, recipient, coins, message):
        transfer = ucoin.wrappers.transactions.RawTransfer(
            self.key_fingerprint(),
            recipient.fingerprint,
            coins,
            message,
            keyid=self.keyid,
            server=node.server,
            port=node.port)
        return transfer()

    def jsonify_contacts(self):
        data = []
        for p in self.contacts:
            data.append(p.jsonify())
        return data

    def jsonify(self):
        data = {'name': self.name,
                'keyId': self.keyid,
                'communities': self.communities.jsonify(self.wallets),
                'contacts': self.jsonify_contacts()}
        return data
