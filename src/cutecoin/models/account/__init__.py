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
from cutecoin.models.transaction import factory as trxFactory

class Account(object):
    '''
    An account is specific to a pgpKey.
    Each account has only one pgpKey, and a key can
    be locally referenced by only one account.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.pgpKeyId = ""
        self.name = ""
        self.communities = Communities()
        self.wallets = Wallets()

    def addWallet(name, currency):
        self.wallets.addWallet(name, currency)

    def keyFingerprint(self):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys()
        logging.debug(self.pgpKeyId)
        for k in availableKeys:
            logging.debug(k)
            if k['keyid'] == self.pgpKeyId:
                return k['fingerprint']
        return ""

    def transactionsReceived(self):
        received = []
        for community in self.communities.communitiesList:
            transactionsData = community.ucoinRequest(ucoin.hdc.transactions.Recipient(self.keyFingerprint()))
            for trxData in transactionsData:
                received.append(trxFactory.createTransaction(trxData['sender'], trxData['number']))
        return received

    def transactionsSent(self):
        sent = []
        for community in self.communities.communitiesList:
            transactionsData = community.ucoinRequest(ucoin.hdc.transactions.sender.Last(self.keyFingerprint(), 20))
            for trxData in transactionsData:
                # Small bug in ucoinpy library
                if not isinstance(trxData, str):
                    sent.append(trxFactory.createTransaction(trxData['sender'], trxData['number']))
        return sent

    def lastIssuances(self, community):
        issuances = []
        if community in self.communities.communitiesList:
            issuancesData = community.ucoinRequest(ucoin.hdc.transactions.sender.Issuance(self.keyFingerprint()))
            for issuance in issuancesData:
                issuances.append(trxFactory.createTransaction(issuance['sender'], issuance['number']))
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
            ucoin.settings['gpg'] = gnupg.GPG()
            issuance = ucoin.wrappers.transactions.Issue(self.keyFingerprint(), community.amendmentNumber(), coins)
            return issuance()

    def jsonify(self):
        data = {'name' : self.name,
                'pgpKeyId' : self.pgpKeyId,
                'communities' : self.communities.jsonify(self.wallets)}
        return data




