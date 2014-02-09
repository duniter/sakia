'''
Created on 1 févr. 2014

@author: inso
'''

class Transaction(object):
    '''
    classdocs
    '''


    def __init__(self, senderFingerprint, increment):
        '''
        Constructor
        '''
        self.senderFingerprint = senderFingerprint
        self.increment = increment

    def transactionID(self):
        return self.senderFingerprint + "-" + self.increment
