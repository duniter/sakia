'''
Created on 1 févr. 2014

@author: inso
'''

import os
import logging
import json

from cutecoin.core import config
from cutecoin.tools.exceptions import KeyAlreadyUsed
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
        self.current_account = None
        config.parse_arguments(argv)
        self.load()

    def get_account(self, name):
        for a in self.accounts:
            logging.debug('Name : ' + a.name + '/' + name)
            if name == a.name:
                return a

    def add_account(self, account):
        for a in self.accounts:
            if a.keyid == account.keyid:
                raise KeyAlreadyUsed(account, account.keyid, a)

        self.accounts.append(account)
        self.current_account = account

    def del_account(self, account):
        self.accounts.remove(account)

    def load(self):
        if not os.path.exists(config.parameters['home']):
            logging.info("Creating home directory")
            os.makedirs((config.parameters['home']))

        if (os.path.exists(config.parameters['data'])
                and os.path.isfile(config.parameters['data'])):
            json_data = open(config.parameters['data'], 'r')
            data = json.load(json_data)
            json_data.close()

            for accountData in data['localAccounts']:
                self.accounts.append(Account.load(accountData))

    def save(self):
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent=4, sort_keys=True)

    def jsonify_accounts(self):
        data = []
        for account in self.accounts:
            data.append(account.jsonify())
        return data

    def jsonify(self):
        data = {'localAccounts': self.jsonify_accounts()}
        return data
