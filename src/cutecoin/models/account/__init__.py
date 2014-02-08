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
            #TODO: Gerer le cas ou plusieurs noeuds sont presents dans la liste et le 0 ne repond pas
            wallet.refreshCoins(community.knownNodes[0], self.keyFingerprint())

        self.receivedTransactions = []
        self.sentTransactions = []

    def addWallet(name, currency):
        self.wallets.addWallet(name, currency)

    def keyFingerprint():
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys(True)
        for k in availableKeys:
            if k['key_id'] == self.pgpKey:
                return k['fingerprint']
        return ""



