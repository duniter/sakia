'''
Created on 1 févr. 2014

@author: inso
'''

import os
import logging
import json
import tarfile

from cutecoin.core import config
from cutecoin.tools.exceptions import NameAlreadyExists, BadAccountFile
from cutecoin.core.account import Account


class Application(object):

    '''
    Managing core application datas :
    Accounts list and general configuration
    '''

    def __init__(self, argv):
        '''
        Constructor
        '''
        self.accounts = {}
        self.default_account = ""
        self.current_account = None
        config.parse_arguments(argv)
        self.load()
        if self.default_account != "":
            self.change_current_account(self.get_account(self.default_account))

    def get_account(self, name):
        if not self.accounts[name]:
            self.load_account(name)
        if name in self.accounts.keys():
            return self.accounts[name]
        else:
            return None

    def create_account(self, name):
        for a in self.accounts:
            if a.name == name:
                raise NameAlreadyExists(a)

        account_path = os.path.join(config.parameters['home'], name)
        if not os.path.exists(account_path):
            logging.info("Creating account directory")
            os.makedirs(account_path)
        account = Account.create(name,
                                 [],
                                 [],
                                 config.parameters)
        self.accounts.append(account)
        self.current_account = account
        return account

    def del_account(self, account):
        self.accounts.remove(account)

    def change_current_account(self, account):
        if self.current_account is not None:
            self.save_cache(self.current_account)
        self.current_account = account
        self.load_cache(account)

    def load(self):
        if not os.path.exists(config.parameters['home']):
            logging.info("Creating home directory")
            os.makedirs((config.parameters['home']))

        if (os.path.exists(config.parameters['data'])
                and os.path.isfile(config.parameters['data'])):
            logging.debug("Loading data...")
            with open(config.parameters['data'], 'r') as json_data:
                data = json.load(json_data)
                json_data.close()
                if 'default_account' in data.keys():
                    self.default_account = data['default_account']
                for account_name in data['local_accounts']:
                    self.accounts[account_name] = None

    def load_account(self, account_name):
        account_path = os.path.join(config.parameters['home'],
                                    account_name, 'properties')
        with open(account_path, 'r') as json_data:
            data = json.load(json_data)
            account = Account.load(data)
            self.accounts[account_name] = account

    def load_cache(self, account):
        for wallet in account.wallets:
            wallet_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__', wallet.pubkey)
            if os.path.exists(wallet_path):
                json_data = open(wallet_path, 'r')
                data = json.load(json_data)
                wallet.cache.load_from_json(data)

    def save(self, account):
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent=4, sort_keys=True)

        account_path = os.path.join(config.parameters['home'],
                                    account.name, 'properties')
        with open(account_path, 'w') as outfile:
            json.dump(account.jsonify(), outfile, indent=4, sort_keys=True)

    def save_cache(self, account):
        if not os.path.exists(os.path.join(config.parameters['home'],
                                        account.name, '__cache__')):
            os.makedirs(os.path.join(config.parameters['home'],
                                        account.name, '__cache__'))
        for wallet in account.wallets:
            wallet_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__', wallet.pubkey)
            with open(wallet_path, 'w') as outfile:
                json.dump(wallet.cache.jsonify(), outfile, indent=4, sort_keys=True)

    def import_account(self, file, name):
        with tarfile.open(file, "r") as tar:
            path = os.path.join(config.parameters['home'],
                                name)
            for obj in ["properties"]:
                try:
                    tar.getmember(obj)
                except KeyError:
                    raise BadAccountFile(file)
            tar.extractall(path)

        account_path = os.path.join(config.parameters['home'],
                                    name, 'properties')
        json_data = open(account_path, 'r')
        data = json.load(json_data)
        account = Account.load(data)
        account.name = name
        self.accounts.append(account)
        self.save(account)

    def export_account(self, file, account):
        with tarfile.open(file, "w") as tar:
            for file in ["properties"]:
                path = os.path.join(config.parameters['home'],
                                    account.name, file)
                tar.add(path, file)

    def jsonify_accounts(self):
        data = []
        logging.debug("{0}".format(self.accounts))
        for account in self.accounts:
            data.append(account)
        return data

    def jsonify(self):
        data = {'default_account': self.default_account,
                'local_accounts': self.jsonify_accounts()}
        return data
