'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import gnupg
from cutecoin.models.account.wallets import Wallets

class Account(object):
    '''
    classdocs
    '''

    def __init__(self, pgpKey, name, communities):
        '''
        Constructor
        '''
        self.pgpKey = pgpKey
        self.name = name
        self.communities = communities
        self.wallets = Wallets()
        for community in self.communities.communitiesList:
            wallet = self.wallets.addWallet(community.currency)
            wallet.refreshCoins(community, self.keyFingerprint())

        self.receivedTransactions = []
        self.sentTransactions = []

    def addWallet(name, currency):
        self.wallets.addWallet(name, currency)

    def keyFingerprint(self):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys()
        for k in availableKeys:
            if k['keyid'] == self.pgpKey:
                return k['fingerprint']
        return ""

    def transactionsReceived(self):
        pass

    def transactionsSent(self):
        pass



