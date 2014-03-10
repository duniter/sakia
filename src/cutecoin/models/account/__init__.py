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

class Account(object):
    '''
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    '''
    def __init__(self, keyId, name, communities, wallets, contacts):
        '''
        Constructor
        '''
        self.keyId = keyId
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts

    @classmethod
    def create(cls, keyId, name, communities):
        '''
        Constructor
        '''
        wallets = Wallets()
        account = cls(keyId, name, communities, wallets, [])
        for community in account.communities.communitiesList:
            wallet = account.wallets.addWallet(community.currency)
            wallet.refreshCoins(community, account.keyFingerprint())
        return account

    @classmethod
    def load(cls, jsonData):
        keyId = jsonData['keyId']
        name = jsonData['name']
        communities = Communities()
        wallets = Wallets()
        contacts = []

        for contactData in jsonData['contacts']:
            contacts.append(Person.fromJson(contactData))

        account = cls(keyId, name, communities, wallets, contacts)

        for communityData in jsonData['communities']:
            account.communities.communitiesList.append(Community.load(communityData, account))

        return account

    def __eq__(self, other):
        if other is not None:
            return other.keyId == self.keyId
        else:
            return False

    def addWallet(self, name, currency):
        self.wallets.addWallet(name, currency)

    def addContact(self, person):
        self.contacts.append(person)

    def keyFingerprint(self):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys()
        logging.debug(self.keyId)
        for k in availableKeys:
            logging.debug(k)
            if k['keyid'] == self.keyId:
                return k['fingerprint']
        return ""

    def transactionsReceived(self):
        received = []
        for community in self.communities.communitiesList:
            transactionsData = community.ucoinRequest(ucoin.hdc.transactions.Recipient(self.keyFingerprint()))
            for trxData in transactionsData:
                received.append(factory.createTransaction(trxData['value']['transaction']['sender'], trxData['value']['transaction']['number'], community))
        return received

    def transactionsSent(self):
        sent = []
        for community in self.communities.communitiesList:
            transactionsData = community.ucoinRequest(ucoin.hdc.transactions.sender.Last(self.keyFingerprint(), 20))
            for trxData in transactionsData:
                # Small bug in ucoinpy library
                if not isinstance(trxData, str):
                    sent.append(factory.createTransaction(trxData['value']['transaction']['sender'], trxData['value']['transaction']['number'], community))
        return sent

    def lastIssuances(self, community):
        issuances = []
        if community in self.communities.communitiesList:
            issuancesData = community.ucoinRequest(ucoin.hdc.transactions.sender.Issuance(self.keyFingerprint()))
            for issuance in issuancesData:
                logging.debug(issuance)
                issuances.append(factory.createTransaction(issuance['value']['transaction']['sender'], issuance['value']['transaction']['number'], community))
        return issuances

    def issuedLastDividend(self, community):
        currentAmendmentNumber = community.amendmentNumber()

        if community in self.communities.communitiesList:
            dividendsData = community.ucoinRequest(ucoin.hdc.transactions.sender.issuance.Dividend(self.keyFingerprint(), currentAmendmentNumber))
            for dividend in dividendsData:
                # Small bug in ucoinpy library
                if not isinstance(dividend, str):
                    return True

        return False

    def issueDividend(self, community, coins):
        if community in self.communities.communitiesList:
            logging.debug(coins)
            issuance = ucoin.wrappers.transactions.Issue(self.keyFingerprint(), community.amendmentNumber(), coins, keyId=self.pgpKeyId)
            return issuance()

    def transferCoins(self, node, recipient, coins, message):
        transfer = ucoin.wrappers.transactions.RawTransfer(self.keyFingerprint(), recipient.fingerprint, coins, message, keyid=self.pgpKeyId, server=node.server, port=node.port)
        return transfer()

    def jsonifyContacts(self):
        data = []
        for p in self.contacts:
            data.append(p.jsonify())
        return data

    def jsonify(self):
        data = {'name' : self.name,
                'keyId' : self.keyId,
                'communities' : self.communities.jsonify(self.wallets),
                'contacts' : self.jsonifyContacts()}
        return data




