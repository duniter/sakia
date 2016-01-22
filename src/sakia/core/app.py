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
import aiohttp

from PyQt5.QtCore import QObject, pyqtSignal, QTranslator, QCoreApplication, QLocale
from ucoinpy.api.bma import API
from aiohttp.connector import ProxyConnector
from . import config
from .account import Account
from .registry import IdentitiesRegistry, Identity
from .. import __version__
from ..tools.exceptions import NameAlreadyExists, BadAccountFile
from ..tools.decorators import asyncify
import i18n_rc


class Application(QObject):

    """
    Managing core application datas :
    Accounts list and general configuration
    Saving and loading the application state
    """

    version_requested = pyqtSignal()
    view_identity_in_wot = pyqtSignal(Identity)

    def __init__(self, qapp, loop, identities_registry):
        """
        Init a new "sakia" application
        :param QCoreApplication qapp: Qt Application
        :param quamash.QEventLoop loop: quamash.QEventLoop instance
        :param sakia.core.registry.IdentitiesRegistry identities_registry: IdentitiesRegistry instance
        :return:
        """

        super().__init__()
        self.qapp = qapp
        self.accounts = {}
        self.current_account = None
        self.loop = loop
        self.available_version = (True,
                                  __version__,
                                  "")
        self._translator = QTranslator(self.qapp)
        self._identities_registry = identities_registry
        self.preferences = {'account': "",
                            'lang': 'en_GB',
                            'ref': 0,
                            'expert_mode': False,
                            'digits_after_comma': 6,
                            'maximized': False,
                            'notifications': True,
                            'enable_proxy': False,
                            'proxy_type': "HTTP",
                            'proxy_address': "",
                            'proxy_port': 8080,
                            'international_system_of_units': True,
                            'auto_refresh': False
                            }

    @classmethod
    def startup(cls, argv, qapp, loop):
        config.parse_arguments(argv)
        identities_registry = IdentitiesRegistry()
        app = cls(qapp, loop, identities_registry)
        app.load()
        app.switch_language()
        app.set_proxy()
        app.get_last_version()
        if app.preferences["account"] != "":
            account = app.get_account(app.preferences["account"])
            app.change_current_account(account)
        # no default account...
        else:
            # if at least one account exists, set it as default...
            if len(app.accounts) > 0:
                # capture names sorted alphabetically
                names = list(app.accounts.keys())
                names.sort()
                # set first name in list as default in preferences
                app.preferences['account'] = names[0]
                app.save_preferences(app.preferences)
                # open it
                logging.debug("No default account in preferences. Set %s as default account." % names[0])

        return app

    def set_proxy(self):
        if self.preferences['enable_proxy'] is True:
            API.aiohttp_connector = ProxyConnector("http://{0}:{1}".format(
                                    self.preferences['proxy_address'],
                                    self.preferences['proxy_port']))
        else:
            API.aiohttp_connector = None

    def switch_language(self):
        logging.debug("Loading translations")
        locale = self.preferences['lang']
        QLocale.setDefault(QLocale(locale))
        QCoreApplication.removeTranslator(self._translator)
        self._translator = QTranslator(self.qapp)
        if locale == "en_GB":
            QCoreApplication.installTranslator(self._translator)
        elif self._translator.load(":/i18n/{0}".format(locale)):
            if QCoreApplication.installTranslator(self._translator):
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

    def add_account(self, account):
        self.accounts[account.name] = account

    def delete_account(self, account):
        """
        Delete an account.
        Current account changes to None if it is deleted.
        """
        account.stop_coroutines()
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

        :param sakia.core.Account account: The account object to display
        .. note:: Emits the application pyqtSignal loading_progressed
        during cache refresh
        """
        if self.current_account is not None:
            self.stop_current_account()

        self.current_account = account
        if self.current_account is not None:
            self.current_account.start_coroutines()

    def stop_current_account(self):
        """
        Save the account to the cache
        and stop the coroutines
        """
        self.save_cache(self.current_account)
        self.save_notifications(self.current_account)
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
            account = Account.load(data, self._identities_registry)
            self.load_cache(account)
            self.accounts[account_name] = account

            for community in account.communities:
                community.network.blockchain_rollback.connect(community.rollback_cache)
                community.network.new_block_mined.connect(lambda b, co=community:
                                                          account.refresh_transactions(self, co))
                community.network.blockchain_rollback.connect(lambda b, co=community:
                                                              account.rollback_transaction(self, co))
                community.network.root_nodes_changed.connect(lambda acc=account: self.save(acc))

        account_notifications_path = os.path.join(config.parameters['home'],
                                    account_name, '__notifications__')

        try:
            with open(account_notifications_path, 'r') as json_data:
                data = json.load(json_data)
                account.notifications = data
        except FileNotFoundError:
            logging.debug("Could not find notifications file")
            pass

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
                    logging.debug("Merging network : {0}".format(data))
                    community.network.merge_with_json(data['network'])

            if os.path.exists(bma_path):
                with open(bma_path, 'r') as json_data:
                    data = json.load(json_data)
                    community.bma_access.load_from_json(data['cache'])

        for wallet in account.wallets:
            for c in account.communities:
                wallet.init_cache(self, c)
            wallet_path = os.path.join(config.parameters['home'],
                                        account.name, '__cache__', wallet.pubkey + "_wal")
            if os.path.exists(wallet_path):
                with open(wallet_path, 'r') as json_data:
                    data = json.load(json_data)
                    wallet.load_caches(self, data)

    def load_preferences(self):
        """
        Load the preferences.
        """
        try:
            preferences_path = os.path.join(config.parameters['home'],
                                            'preferences')
            with open(preferences_path, 'r') as json_data:
                data = json.load(json_data)
                for key in data:
                    self.preferences[key] = data[key]
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

        self.set_proxy()

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

    def save_notifications(self, account):
        """
        Save an account notifications

        :param account: The account object to save
        """
        account_path = os.path.join(config.parameters['home'],
                                account.name)
        notifications_path = os.path.join(account_path, '__notifications__')
        with open(notifications_path, 'w') as outfile:
            json.dump(account.notifications, outfile, indent=4, sort_keys=True)

    def save_registries(self):
        """
        Save the registries
        """
        identities_path = os.path.join(config.parameters['home'],
                                    '__identities__')
        buffer_path = identities_path + ".buf"
        with open(buffer_path, 'w') as outfile:
            data = self.identities_registry.jsonify()
            data['version'] = __version__
            for chunk in json.JSONEncoder().iterencode(data):
                outfile.write(chunk)
        shutil.move(buffer_path, identities_path)

    def save_wallet(self, account, wallet):
        """
        Save wallet of account in cache

        :param sakia.core.account.Account account: Account instance
        :param sakia.core.wallet.Wallet wallet: Wallet instance
        """
        if not os.path.exists(os.path.join(config.parameters['home'],
                                           account.name, '__cache__')):
            os.makedirs(os.path.join(config.parameters['home'],
                                     account.name, '__cache__'))
        wallet_path = os.path.join(config.parameters['home'],
                                   account.name, '__cache__', wallet.pubkey + "_wal")
        buffer_path = wallet_path + ".buf"
        with open(buffer_path, 'w') as outfile:
            data = wallet.jsonify_caches()
            data['version'] = __version__
            for chunk in json.JSONEncoder().iterencode(data):
                outfile.write(chunk)
        shutil.move(buffer_path, wallet_path)

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
            buffer_path = network_path + ".buf"

            with open(buffer_path, 'w') as outfile:
                data = dict()
                data['network'] = community.network.jsonify()
                data['version'] = __version__
                for chunk in json.JSONEncoder().iterencode(data):
                    outfile.write(chunk)
            shutil.move(buffer_path, network_path)

            buffer_path = bma_path + ".buf"

            with open(buffer_path, 'w') as outfile:
                data['cache'] = community.bma_access.jsonify()
                data['version'] = __version__
                for chunk in json.JSONEncoder().iterencode(data):
                    outfile.write(chunk)
            shutil.move(buffer_path, bma_path)

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
        account = Account.load(data, self._identities_registry)
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

    @asyncify
    async def get_last_version(self):
        if self.preferences['enable_proxy'] is True:
            connector = ProxyConnector("http://{0}:{1}".format(
                                    self.preferences['proxy_address'],
                                    self.preferences['proxy_port']))
        else:
            connector = None
        try:
            with aiohttp.Timeout(15):
                response = await aiohttp.get("https://api.github.com/repos/ucoin-io/sakia/releases", connector=connector)
                if response.status == 200:
                    releases = await response.json()
                    latest = None
                    for r in releases:
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
        except (aiohttp.errors.ClientError, aiohttp.errors.TimeoutError) as e:
            logging.debug("Could not connect to github : {0}".format(str(e)))
        except Exception as e:
            pass
