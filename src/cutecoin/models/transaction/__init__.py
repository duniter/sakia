'''
Created on 1 févr. 2014

@author: inso
'''

class Transaction(object):
    '''
    classdocs
    '''


    def __init__(self, value, sender, receiver, currency):
        '''
        Constructor
        '''
        self.value = value
        self.sender = sender
        self.receiver = receiver
        self.currency = currency
