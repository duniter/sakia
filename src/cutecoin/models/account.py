'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Account(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.transactionNodes = []
        self.trustableNodes = []

    def addTransactionNode(self, node):
        self.transactionNodes.append(node)

    def addTrustableNode(self, node):
        self.trustableNodes.append(node)


