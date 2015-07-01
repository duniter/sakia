"""
Created on 1 févr. 2014

@author: inso
"""

import os
import logging
import tarfile
import shutil
import json
import datetime
import i18n_rc

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, \
QUrl, QTranslator, QCoreApplication, QLocale
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import config
from .account import Account
from .registry.identities import IdentitiesRegistry
from .. import __version__
from ..tools.exceptions import NameAlreadyExists, BadAccountFile


class Application(QObject):

    """
    Managing core application datas :
    Accounts list and general configuration
    Saving and loading the application state
    """

    version_requested = pyqtSignal()

    def __init__(self, qapp, loop, network_manager, identities_registry):
        """
        Create a new "cutecoin" application

        :param argv: The argv parameters of the call
        """
        super().__init__()
        self.qapp = qapp
        self.accounts = {}
        self.current_account = None
        self.loop = loop
        self.available_version = (True,
                                  __version__,
                                  "")
        self._identities_registry = identities_registry
        self._network_manager = network_manager
        self.preferences = {'account': "",
                            'lang': 'en_GB',
                            'ref': 0
                            }

    @classmethod
    def startup(cls, argv, qapp, loop):
        config.parse_arguments(argv)
        network_manager = QNetworkAccessManager()
        identities_registry = IdentitiesRegistry()
        app = cls(qapp, loop, network_manager, identities_registry)

        app.load()
        app.switch_language()
        return app


    def switch_language(self):
        translator = QTranslator(self.qapp)
        logging.debug("Loading translations")
        locale = self.preferences['lang']
        QLocale.setDefault(QLocale(locale))
        if translator.load(":/i18n/{0}".format(locale)):
            if QCoreApplication.installTranslator(translator):
                logging.debug("Loaded i18n/{0}".format(locale))
        else:
            logging.debug("Couldn't load translation")

    def get_account(self, name):
        """
        Load an account then return it

        :param str name: The account name
        :return: The loaded account if it's a success, else return None
        """
        if name in self.accounts.keys():
            self.load_account(name)
            return self.accounts[name]
        else:
            return None

    def create_account(self, name):
        """
        Create a new account from its name

        :param str name: The account name
        :return: The new account
        :raise: NameAlreadyExists if the account name is already used locally
        """
        for a in self.accounts:
            if a == name:
                raise NameAlreadyExists(a)

        account = Account.create(name, self._identities_registry)

        return account

    @property
    def identities_registry(self):
        return self._identities_registry

    @property
    def network_manager(self):
        return self._network_manager

    def add_account(self, account):
        self.accounts[account.name] = account

    def delete_account(self, account):
        """
        Delete an account.
        Current account changes to None if it is deleted.
        """
        self.accounts.pop(account.name)
        if self.current_account == account:
            self.current_account = None
        with open(config.parameters['data'], 'w') as outfile:
            json.dump(self.jsonify(), outfile, indent=4, sort_keys=True)
        if self.preferences['account'] == account.name:
            self.preferences['account'] = ""
            self.save_preferences(self.preferences)

    def change_current_account(self, account):
        """
        Change current account displayed and refresh its cache.

        :param cutecoin.core.Account account: The account object to display
        .. note:: Emits the application pyqtSignal loading_progressed
        during cache refresh
        """
        if self.current_account is not None:
            self.stop_current_account()

        self.current_account = account

    def stop_current_account(self):
        """
        Save the account to the cache
        and stop the coroutines
        """
        self.save_cache(self.current_account)
        self.current_account.stop_coroutines()

    def load(self):
        """
        Load a saved application state from the data file.
        Loads only jsonified objects but not their cache.

        If the standard application state file can't be found,
        no error is raised.
        """
        self.load_registries()
        self.load_preferences()
        try:
            logging.debug("Loading data...")
            with open(config.parameters['data'], 'r') as json_data:
                data = json.load(json_data)
                for account_name in data['local_accounts']:
                    self.accounts[account_name] = None
        except FileNotFoundError:
            pass

    def load_registries(self):
        """
        Load the Person instances of the person module.
        Each instance is unique, and can be find by its public key.
        """
        try:
            identities_path = os.path.join(config.parameters['home'],
                                        '__identities__')
            with open(identities_path, 'r') as identities_data:
                data = json.load(identities_data)
                self._identities_registry.load_json(data)
        except FileNotFoundError:
            pass

    def load_account(self, account_name):
        """
        Load an account from its name

        :param str account_name: The account name
        """
        account_path = os.path.join(config.parameters['home'],
                                    account_name, 'properties')
        with open(account_path, 'r') as json_data:
            data = json.load(json_data)
            account = Account.load(data, self._network_manager, self._identities_registry)
            self.load_cache(account)
            self.accounts[account_name] = account

    def load_cache(self, account):
        """
        Load an account cache

        :param account: The account object to load the cache
        """
        for community in account.communities:
            bma_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_bma')

            network_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_network')

            if os.path.exists(network_path):
                with open(network_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    logging.debug("Merging network : {0}".format(data))
                    community.network.merge_with_json(data['network'])
                else:
                    os.remove(network_path)

            if os.path.exists(bma_path):
                with open(bma_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    community.bma_access.load_from_json(data['cache'])
                else:
                    os.remove(bma_path)

        for wallet in account.wallets:
            for c in account.communities:
                wallet.init_cache(c)
            wallet_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__', wallet.pubkey + "_wal")
            if os.path.exists(wallet_path):
                with open(wallet_path, 'r') as json_data:
                    data = json.load(json_data)
                if 'version' in data and data['version'] == __version__:
                    wallet.load_caches(data)
                else:
                    os.remove(wallet_path)

    def load_preferences(self):
        """
        Load the preferences.
        """

        try:
            preferences_path = os.path.join(config.parameters['home'],
                                            'preferences')
            with open(preferences_path, 'r') as json_data:
                data = json.load(json_data)
                self.preferences = data
        except FileNotFoundError:
            pass

    def save_preferences(self, preferences):
        """
        Save the preferences.

        :param preferences: A dict containing the keys/values of the preferences
        """
        assert('lang' in preferences)
        assert('account' in preferences)
        assert('ref' in preferences)

        self.preferences = preferences
        preferences_path = os.path.join(config.parameters['home'],
                                        'preferences')
        with open(preferences_path, 'w') as outfile:
            json.dump(preferences, outfile, indent=4)

    def save(self, account):
        """
        Save an account

        :param account: The account object to save
        """
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

    def save_registries(self):
        """
        Save the registries
        """
        identities_path = os.path.join(config.parameters['home'],
                                    '__identities__')
        with open(identities_path, 'w')as outfile:
            data = self.identities_registry.jsonify()
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
                                   account.name, '__cache__', wallet.pubkey + "_wal")
        with open(wallet_path, 'w') as outfile:
            data = wallet.jsonify_caches()
            data['version'] = __version__
            json.dump(data, outfile, indent=4, sort_keys=True)

    def save_cache(self, account):
        """
        Save the cache of an account

        :param account: The account object to save the cache
        """
        if not os.path.exists(os.path.join(config.parameters['home'],
                                        account.name, '__cache__')):
            os.makedirs(os.path.join(config.parameters['home'],
                                        account.name, '__cache__'))
        for wallet in account.wallets:
            self.save_wallet(account, wallet)

        for community in account.communities:
            bma_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_bma')

            network_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__',
                                        community.currency + '_network')

            with open(network_path, 'w') as outfile:
                data = dict()
                data['network'] = community.network.jsonify()
                data['version'] = __version__
                json.dump(data, outfile, indent=4, sort_keys=True)

            with open(bma_path, 'w') as outfile:
                data['cache'] = community.bma_access.jsonify()
                data['version'] = __version__
                json.dump(data, outfile, indent=4, sort_keys=True)

    def import_account(self, file, name):
        """
        Import an account from a tar file and open it

        :param str file: The file path of the tar file
        :param str name: The account name
        """
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
        self.change_current_account(account)

    def export_account(self, file, account):
        """
        Export an account to a tar file

        :param str file: The filepath of the tar file
        :param account: The account object to export
        """
        with tarfile.open(file, "w") as tar:
            for file in ["properties"]:
                path = os.path.join(config.parameters['home'],
                                    account.name, file)
                tar.add(path, file)

    def jsonify_accounts(self):
        """
        Jsonify an account

        :return: The account as a dict to format as json
        """
        data = []
        logging.debug("{0}".format(self.accounts))
        for account in self.accounts:
            data.append(account)
        return data

    def jsonify(self):
        """
        Jsonify the app datas

        :return: The accounts of the app to format as json
        """
        data = {'local_accounts': self.jsonify_accounts()}
        return data

    def stop(self):
        if self.current_account:
            self.stop_current_account()

        self.save_registries()

    def get_last_version(self):
        url = QUrl("https://api.github.com/repos/ucoin-io/cutecoin/releases")
        request = QNetworkRequest(url)
        reply = self._network_manager.get(request)
        reply.finished.connect(self.read_available_version)

    @pyqtSlot(QNetworkReply)
    def read_available_version(self):
        latest = None
        reply = self.sender()
        releases = reply.readAll().data().decode('utf-8')
        logging.debug(releases)
        if reply.error() == QNetworkReply.NoError:
            for r in json.loads(releases):
                if not latest:
                    latest = r
                else:
                    latest_date = datetime.datetime.strptime(latest['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                    date = datetime.datetime.strptime(r['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                    if latest_date < date:
                        latest = r
            latest_version = latest["tag_name"]
            version = (__version__ == latest_version,
                       latest_version,
                       latest["html_url"])
            logging.debug("Found version : {0}".format(latest_version))
            logging.debug("Current version : {0}".format(__version__))
            self.available_version = version
        self.version_requested.emit()
