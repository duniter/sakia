'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

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
        self.transactionNodes = []
        self.trustableNodes = []
        self.wallets = []
        self.receivedTransactions = []
        self.sentTransactions = []

    def addTransactionNode(self, node):
        self.transactionNodes.append(node)

    def addTrustableNode(self, node):
        self.trustableNodes.append(node)


