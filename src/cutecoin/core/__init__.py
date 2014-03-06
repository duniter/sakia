'''
Created on 1 févr. 2014

@author: inso
'''

import os
import logging
import json

from cutecoin.core import config
from cutecoin.core.exceptions import KeyAlreadyUsed
from cutecoin.models.account import Account


class Core(object):
    '''
    Managing core application datas :
    Accounts list and general configuration
    '''
    def __init__(self, argv):
        '''
        Constructor
        '''
        self.accounts = []
        self.currentAccount = None
        config.parseArguments(argv)
        self.load()

    def getAccount(self, name):
        for a in self.accounts:
            logging.debug('Name : ' + a.name + '/' + name)
            if name == a.name:
                return a

    def addAccount(self, account):
        for a in self.accounts:
            if a.keyId == account.keyId:
                raise KeyAlreadyUsed(account, account.keyId, a)

        self.accounts.append(account)
        self.currentAccount = account

    def delAccount(self, account):
        self.accounts.remove(account)


    def load(self):
        if not os.path.exists(config.parameters['home']):
            logging.info("Creating home directory")
            os.makedirs((config.parameters['home']))

        if (os.path.exists(config.parameters['data'])  \
            and os.path.isfile(config.parameters['data'])):
            json_data=open(config.parameters['data'], 'r')
            data = json.load(json_data)
            json_data.close()

            for accountData in data['localAccounts']:
                self.accounts.append(Account.load(accountData))

    def save(self):
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent = 4, sort_keys=True)


    def jsonifyAccounts(self):
        data = []
        for account in self.accounts:
            data.append(account.jsonify())
        return data

    def jsonify(self):
        data = {'localAccounts' : self.jsonifyAccounts()}
        return data

