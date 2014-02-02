'''
Created on 1 févr. 2014

@author: inso
'''

class Wallet(object):
    '''
    classdocs
    '''


    def __init__(self, currency):
        '''
        Constructor
        '''
        self.initialValue = 0
        self.coins = []
        self.currency = currency
