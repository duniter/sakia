'''
Created on 1 févr. 2014

@author: inso
'''

import os
import logging
import json
import tarfile

from . import config
from ..tools.exceptions import NameAlreadyExists, BadAccountFile
from .account import Account
from .. import __version__


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

    def get_account(self, name):
        self.load_account(name)
        if name in self.accounts.keys():
            return self.accounts[name]
        else:
            return None

    def create_account(self, name):
        for a in self.accounts:
            if a == name:
                raise NameAlreadyExists(a)

        account_path = os.path.join(config.parameters['home'], name)
        if not os.path.exists(account_path):
            logging.info("Creating account directory")
            os.makedirs(account_path)
        account = Account.create(name,
                                 [],
                                 [],
                                 config.parameters)

        self.accounts[name] = account
        self.current_account = account
        return account

    def del_account(self, account):
        self.accounts.remove(account)

    def change_current_account(self, account):
        if self.current_account is not None:
            self.save_cache(self.current_account)

        account.refresh_cache()
        self.current_account = account

    def load(self):
        if (os.path.exists(config.parameters['data'])
                and os.path.isfile(config.parameters['data'])):
            logging.debug("Loading data...")
            with open(config.parameters['data'], 'r') as json_data:
                data = json.load(json_data)
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
            self.load_cache(account)
            self.accounts[account_name] = account

    def load_cache(self, account):
        for wallet in account.wallets:
            wallet_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__', wallet.pubkey)
            if os.path.exists(wallet_path):
                with open(wallet_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    wallet.load_caches(data)
                else:
                    os.remove(wallet_path)
            for community in account.communities:
                wallet.refresh_cache(community)

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
                data = wallet.jsonify_caches()
                data['version'] = __version__
                json.dump(data, outfile, indent=4, sort_keys=True)

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
