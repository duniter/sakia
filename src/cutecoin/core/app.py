'''
Created on 1 févr. 2014

@author: inso
'''

import os
import logging
import tarfile
import shutil
import json
import datetime
import sys

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import config
from .account import Account
from . import person
from .watching.monitor import Monitor
from .. import __version__
from ..tools.exceptions import NameAlreadyExists, BadAccountFile


class Application(QObject):

    '''
    Managing core application datas :
    Accounts list and general configuration
    Saving and loading the application state
    '''

    loading_progressed = pyqtSignal(int, int)
    version_requested = pyqtSignal()

    def __init__(self, argv):
        '''
        Create a new "cutecoin" application

        :param argv: The argv parameters of the call
        '''
        super().__init__()
        self.accounts = {}
        self.default_account = ""
        self.current_account = None
        self.monitor = None
        self.available_version = __version__
        config.parse_arguments(argv)
        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self.read_available_version)
        self.get_last_version()
        self.load()

    def get_account(self, name):
        '''
        Load an account then return it

        :param str name: The account name
        :return: The loaded account if it's a success, else return None
        '''
        self.load_account(name)
        if name in self.accounts.keys():
            return self.accounts[name]
        else:
            return None

    def create_account(self, name):
        '''
        Create a new account from its name

        :param str name: The account name
        :return: The new account
        :raise: NameAlreadyExists if the account name is already used locally
        '''
        for a in self.accounts:
            if a == name:
                raise NameAlreadyExists(a)

        account = Account.create(name)

        return account

    def add_account(self, account):
        self.accounts[account.name] = account

    def delete_account(self, account):
        '''
        Delete an account.
        Current account changes to None if it is deleted.
        '''
        self.accounts.pop(account.name)
        if self.current_account == account:
            self.current_account = None
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent=4, sort_keys=True)

    def change_current_account(self, account):
        '''
        Change current account displayed and refresh its cache.

        :param account: The account object to display
        .. note:: Emits the application pyqtSignal loading_progressed
        during cache refresh
        '''
        def progressing(value, maximum):
            self.loading_progressed.emit(value, maximum)

        if self.current_account is not None:
            if self.monitor:
                self.monitor.stop_watching()
            self.save_cache(self.current_account)
        account.loading_progressed.connect(progressing)
        account.refresh_cache()
        self.monitor = Monitor(account)
        self.monitor.prepare_watching()
        self.current_account = account

    def load(self):
        '''
        Load a saved application state from the data file.
        Loads only jsonified objects but not their cache.

        If the standard application state file can't be found,
        no error is raised.
        '''
        self.load_persons()
        try:
            logging.debug("Loading data...")
            with open(config.parameters['data'], 'r') as json_data:
                data = json.load(json_data)
                if 'default_account' in data.keys():
                    self.default_account = data['default_account']
                for account_name in data['local_accounts']:
                    self.accounts[account_name] = None
        except FileNotFoundError:
            pass

    def load_persons(self):
        '''
        Load the Person instances of the person module.
        Each instance is unique, and can be find by its public key.
        '''
        try:
            persons_path = os.path.join(config.parameters['home'],
                                        '__persons__')
            with open(persons_path, 'r') as persons_path:
                data = json.load(persons_path)
                person.load_cache(data)
        except FileNotFoundError:
            pass

    def load_account(self, account_name):
        '''
        Load an account from its name

        :param str account_name: The account name
        '''
        account_path = os.path.join(config.parameters['home'],
                                    account_name, 'properties')
        with open(account_path, 'r') as json_data:
            data = json.load(json_data)
            account = Account.load(data)
            self.load_cache(account)
            self.accounts[account_name] = account

    def load_cache(self, account):
        '''
        Load an account cache

        :param account: The account object to load the cache
        '''
        for community in account.communities:
            community_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency)

            network_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_network')

            if os.path.exists(network_path):
                with open(network_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    logging.debug("Merging network : {0}".format(data))
                    community.load_merge_network(data['network'])
                else:
                    os.remove(network_path)

            if os.path.exists(community_path):
                with open(community_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    community.load_cache(data)
                else:
                    os.remove(community_path)

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

    def save(self, account):
        '''
        Save an account

        :param account: The account object to save
        '''
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent=4, sort_keys=True)
        account_path = os.path.join(config.parameters['home'],
                                account.name)
        if account.name in self.accounts:
            properties_path = os.path.join(account_path, 'properties')
            if not os.path.exists(account_path):
                logging.info("Creating account directory")
                os.makedirs(account_path)
            with open(properties_path, 'w') as outfile:
                json.dump(account.jsonify(), outfile, indent=4, sort_keys=True)
        else:
            account_path = os.path.join(config.parameters['home'], account.name)
            shutil.rmtree(account_path)

    def save_persons(self):
        '''
        Save the person module cache
        '''
        persons_path = os.path.join(config.parameters['home'],
                                    '__persons__')
        with open(persons_path, 'w')as outfile:
            data = person.jsonify_cache()
            data['version'] = __version__
            json.dump(data, outfile, indent=4, sort_keys=True)

    def save_wallet(self, account, wallet):
        """
        Save wallet of account in cache

        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.wallet.Wallet wallet: Wallet instance
        """
        if not os.path.exists(os.path.join(config.parameters['home'],
                                           account.name, '__cache__')):
            os.makedirs(os.path.join(config.parameters['home'],
                                     account.name, '__cache__'))
        wallet_path = os.path.join(config.parameters['home'],
                                   account.name, '__cache__', wallet.pubkey)
        with open(wallet_path, 'w') as outfile:
            data = wallet.jsonify_caches()
            data['version'] = __version__
            json.dump(data, outfile, indent=4, sort_keys=True)

    def save_cache(self, account):
        '''
        Save the cache of an account

        :param account: The account object to save the cache
        '''
        if not os.path.exists(os.path.join(config.parameters['home'],
                                        account.name, '__cache__')):
            os.makedirs(os.path.join(config.parameters['home'],
                                        account.name, '__cache__'))
        for wallet in account.wallets:
            self.save_wallet(account, wallet)

        for community in account.communities:
            community_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency)

            network_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_network')

            with open(network_path, 'w') as outfile:
                data = dict()
                data['network'] = community.jsonify_network()
                data['version'] = __version__
                json.dump(data, outfile, indent=4, sort_keys=True)

            with open(community_path, 'w') as outfile:
                data = community.jsonify_cache()
                data['version'] = __version__
                json.dump(data, outfile, indent=4, sort_keys=True)

    def import_account(self, file, name):
        '''
        Import an account from a tar file

        :param str file: The file path of the tar file
        :param str name: The account name
        '''
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
        self.add_account(account)
        self.save(account)

    def export_account(self, file, account):
        '''
        Export an account to a tar file

        :param str file: The filepath of the tar file
        :param account: The account object to export
        '''
        with tarfile.open(file, "w") as tar:
            for file in ["properties"]:
                path = os.path.join(config.parameters['home'],
                                    account.name, file)
                tar.add(path, file)

    def jsonify_accounts(self):
        '''
        Jsonify an account

        :return: The account as a dict to format as json
        '''
        data = []
        logging.debug("{0}".format(self.accounts))
        for account in self.accounts:
            data.append(account)
        return data

    def jsonify(self):
        '''
        Jsonify the app datas

        :return: The accounts of the app to format as json
        '''
        data = {'default_account': self.default_account,
                'local_accounts': self.jsonify_accounts()}
        return data

    def get_last_version(self):
        url = QUrl("https://api.github.com/repos/ucoin-io/cutecoin/releases")
        request = QNetworkRequest(url)
        self._network_manager.get(request)

    @pyqtSlot(QNetworkReply)
    def read_available_version(self, reply):
        latest = None
        releases = reply.readAll().data().decode('utf-8')
        logging.debug(releases)
        for r in json.loads(releases):
            if not latest:
                latest = r
            else:
                latest_date = datetime.datetime.strptime(latest['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                date = datetime.datetime.strptime(r['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                if latest_date < date:
                    latest = r
        latest_version = tuple(latest["tag_name"].split("."))
        version = (__version__ == latest_version,
                   latest_version,
                   latest["html_url"])
        logging.debug("Found version : {0}".format(latest_version))
        if version != self.available_version:
            self.available_version = version
        self.version_requested.emit()
