'''
Created on 1 févr. 2014

@author: inso
'''

from cutecoin.core.appData import AppData
from cutecoin.core import config

class Core(object):

    def __init__(self, argv):
        '''
        Constructor
        '''
        self.account = []
        self.currentAccount = None
        config.parseArguments(argv)
        AppData().load(self)

    def getAccounts(self):
        return self.accounts

    def addAccount(self, account):
        self.accounts.append(account)
        self.currentAccount = account

    def delAccount(self, account):
        self.accounts.remove(account)

