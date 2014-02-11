'''
Created on 1 févr. 2014

@author: inso
'''

from cutecoin.core import config
from cutecoin.core.exceptions import KeyAlreadyUsed

import json
from cutecoin.core import config
from cutecoin.models.account import factory
import os


class Core(object):

    def __init__(self, argv):
        '''
        Constructor
        '''
        self.accounts = []
        self.currentAccount = None
        config.parseArguments(argv)
        self.load()

    def getAccounts(self):
        return self.accounts

    def addAccount(self, account):
        for a in self.accounts:
            if a.pgpKeyId == account.pgpKeyId:
                raise KeyAlreadyUsed(account, account.pgpKeyId, a)

        self.accounts.append(account)
        self.currentAccount = account

    def delAccount(self, account):
        self.accounts.remove(account)


    def load(self):
        if (os.path.exists(config.data['home'])):
            json_data=open(config.data['home'], 'w+')
            data = json.load(json_data)
            json_data.close()

            for accountData in data['localAccounts']:
                self.accounts.append(factory.loadAccount(accountData))


    def save(self):
        with open(config.data['home'], 'w+') as outfile:
            json.dump(self.jsonify(), outfile, indent = 4, sort_keys=True)




    def jsonifyAccounts(self):
        data = []
        for account in self.accounts:
            data.append(account.jsonify())
        return data

    def jsonify(self):
        data = {'localAccounts' : self.jsonifyAccounts()}
        return data

