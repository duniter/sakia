"""
Created on 1 févr. 2014

@author: inso
"""

import asyncio
import logging

from PyQt5.QtCore import QObject, pyqtSignal
from aiohttp.errors import ClientError
from pkg_resources import parse_version

from duniterpy.api import bma
from duniterpy.api import errors
from duniterpy.api.bma import PROTOCOL_VERSION
from duniterpy.documents import Membership, SelfCertification, Certification, Revocation, BlockUID, Block
from duniterpy.key import SigningKey
from sakia import money
from .community import Community
from .registry import LocalState
from .wallet import Wallet
from .. import __version__
from ..tools.exceptions import ContactAlreadyExists, LookupFailureError


class Account(QObject):
    """
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    """
    loading_progressed = pyqtSignal(Community, int, int)
    loading_finished = pyqtSignal(Community, list)
    wallets_changed = pyqtSignal()
    certification_accepted = pyqtSignal()
    contacts_changed = pyqtSignal()

    def __init__(self, salt, pubkey, name, communities, wallets, contacts, identities_registry):
        """
        Create an account

        :param str salt: The root key salt
        :param str pubkey: Known account pubkey. Used to check that password \
         is OK by comparing (salt, given_passwd) = (pubkey, privkey) \
         with known pubkey
        :param str name: The account name, same as network identity uid
        :param list of sakia.core.Community communities: Community objects referenced by this account
        :param list of sakia.core.Wallet wallets: Wallet objects owned by this account
        :param list of dict contacts: Contacts of this account
        :param sakia.core.registry.IdentitiesRegistry: The identities registry intance

        .. warnings:: The class methods create and load should be used to create an account
        """
        super().__init__()
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts
        self._identities_registry = identities_registry
        self._current_ref = 0

        self.notifications = {'membership_expire_soon':
                                  [
                                      self.tr("Warning : Your membership is expiring soon."),
                                      0
                                   ],
                            'warning_certifications':
                                    [
                                        self.tr("Warning : Your could miss certifications soon."),
                                        0
                                    ],
                            'warning_revokation':
                                    [
                                        self.tr("Warning : If you don't renew soon, your identity will be considered revoked."),
                                        0
                                    ],
                            'warning_certifying_first_time': True,
                            }

    @classmethod
    def create(cls, name, identities_registry):
        """
        Factory method to create an empty account object
        This new account doesn't have any key and it should be given
        one later
        It doesn't have any community nor does it have wallets.
        Communities could be added later, wallets will be managed
        by its wallet pool size.

        :param str name: The account name, same as network identity uid
        :return: A new empty account object
        """
        account = cls(None, None, name, [], [], [], identities_registry)
        return account

    @classmethod
    def load(cls, json_data, identities_registry):
        """
        Factory method to create an Account object from its json view.
        :rtype : sakia.core.account.Account
        :param dict json_data: The account view as a json dict
        :param PyQt5.QtNetwork import QNetworkManager: network_manager
        :param sakia.core.registry.self._identities_registry: identities_registry
        :return: A new account object created from the json datas
        """
        salt = json_data['salt']
        pubkey = json_data['pubkey']
        if 'file_version' in json_data:
            file_version = parse_version(json_data['file_version'])
        else:
            file_version = parse_version('0.11.5')

        name = json_data['name']
        contacts = []

        for contact_data in json_data['contacts']:
            contacts.append(contact_data)

        wallets = []
        for data in json_data['wallets']:
            wallets.append(Wallet.load(data, identities_registry))

        communities = []
        for data in json_data['communities']:
            community = Community.load(data, file_version)
            communities.append(community)

        account = cls(salt, pubkey, name, communities, wallets,
                      contacts, identities_registry)
        return account

    def __eq__(self, other):
        """
        :return: True if account.pubkey == other.pubkey
        """
        if other is not None:
            return other.pubkey == self.pubkey
        else:
            return False

    def check_password(self, password):
        """
        Method to verify the key password validity

        :param str password: The key password
        :return: True if the generated pubkey is the same as the account
        .. warnings:: Generates a new temporary SigningKey
        """
        key = SigningKey(self.salt, password)
        return (key.pubkey == self.pubkey)

    def add_contact(self, new_contact):
        same_contact = [contact for contact in self.contacts
                        if new_contact['pubkey'] == contact['pubkey']]

        if len(same_contact) > 0:
            raise ContactAlreadyExists(new_contact['name'], same_contact[0]['name'])
        self.contacts.append(new_contact)
        self.contacts_changed.emit()

    def edit_contact(self, index, new_data):
        self.contacts[index] = new_data
        self.contacts_changed.emit()

    def remove_contact(self, contact):
        self.contacts.remove(contact)
        self.contacts_changed.emit()

    def add_community(self, community):
        """
        Add a community to the account

        :param community: A community object to add
        """
        self.communities.append(community)
        return community

    def refresh_transactions(self, app, community):
        """
        Refresh the local account cache
        This needs n_wallets * n_communities cache refreshing to end

        .. note:: emit the Account pyqtSignal loading_progressed during refresh
        """
        logging.debug("Start refresh transactions")
        loaded_wallets = 0
        received_list = []
        values = {}
        maximums = {}

        def progressing(value, maximum, hash):
            #logging.debug("Loading = {0} : {1} : {2}".format(value, maximum, loaded_wallets))
            values[hash] = value
            maximums[hash] = maximum
            account_value = sum(values.values())
            account_max = sum(maximums.values())
            self.loading_progressed.emit(community, account_value, account_max)

        def wallet_finished(received):
            logging.debug("Finished loading wallet")
            nonlocal loaded_wallets
            loaded_wallets += 1
            if loaded_wallets == len(self.wallets):
                logging.debug("All wallets loaded")
                self._refreshing = False
                self.loading_finished.emit(community, received_list)
                for w in self.wallets:
                    w.refresh_progressed.disconnect(progressing)
                    w.refresh_finished.disconnect(wallet_finished)

        for w in self.wallets:
            w.refresh_progressed.connect(progressing)
            w.refresh_finished.connect(wallet_finished)
            w.init_cache(app, community)
            w.refresh_transactions(community, received_list)

    def rollback_transaction(self, app, community):
        """
        Refresh the local account cache
        This needs n_wallets * n_communities cache refreshing to end

        .. note:: emit the Account pyqtSignal loading_progressed during refresh
        """
        logging.debug("Start refresh transactions")
        loaded_wallets = 0
        received_list = []
        values = {}
        maximums = {}

        def progressing(value, maximum, hash):
            #logging.debug("Loading = {0} : {1} : {2}".format(value, maximum, loaded_wallets))
            values[hash] = value
            maximums[hash] = maximum
            account_value = sum(values.values())
            account_max = sum(maximums.values())
            self.loading_progressed.emit(community, account_value, account_max)

        def wallet_finished(received):
            logging.debug("Finished loading wallet")
            nonlocal loaded_wallets
            loaded_wallets += 1
            if loaded_wallets == len(self.wallets):
                logging.debug("All wallets loaded")
                self._refreshing = False
                self.loading_finished.emit(community, received_list)
                for w in self.wallets:
                    w.refresh_progressed.disconnect(progressing)
                    w.refresh_finished.disconnect(wallet_finished)

        for w in self.wallets:
            w.refresh_progressed.connect(progressing)
            w.refresh_finished.connect(wallet_finished)
            w.init_cache(app, community)
            w.rollback_transactions(community, received_list)

    def set_display_referential(self, index):
        self._current_ref = index

    def set_scrypt_infos(self, salt, password):
        """
        Change the size of the wallet pool
        :param int size: The new size of the wallet pool
        :param str password: The password of the account, same for all wallets
        """
        self.salt = salt
        self.pubkey = SigningKey(self.salt, password).pubkey
        wallet = Wallet.create(0, self.salt, password,
                               "Wallet", self._identities_registry)
        self.wallets.append(wallet)

    async def identity(self, community):
        """
        Get the account identity in the specified community
        :param sakia.core.community.Community community: The community where to look after the identity
        :return: The account identity in the community
        :rtype: sakia.core.registry.Identity
        """
        identity = await self._identities_registry.future_find(self.pubkey, community)
        if identity.local_state == LocalState.NOT_FOUND:
            identity.uid = self.name
        return identity

    @property
    def current_ref(self):
        return money.Referentials[self._current_ref]

    def transfers(self, community):
        """
        Get all transfers done in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: All account wallets transfers
        """
        sent = []
        for w in self.wallets:
            sent.extend(w.transfers(community))
        return sent

    def dividends(self, community):
        """
        Get all dividends received in this community
        by the first wallet of this account

        :param community: The target community
        :return: All account dividends
        """
        return self.wallets[0].dividends(community)

    async def future_amount(self, community):
        """
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        """
        value = 0
        for w in self.wallets:
            val = await w.future_value(community)
            value += val
        return value

    async def amount(self, community):
        """
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        """
        value = 0
        for w in self.wallets:
            val = await w.value(community)
            value += val
        return value

    def start_coroutines(self):
        for c in self.communities:
            c.start_coroutines()

    async def stop_coroutines(self, closing=False):
        logging.debug("Stop communities coroutines")
        for c in self.communities:
            await c.stop_coroutines(closing)

        logging.debug("Stop wallets coroutines")
        for w in self.wallets:
            w.stop_coroutines(closing)
        logging.debug("Account coroutines stopped")

    def jsonify(self):
        """
        Get the account in a json format.

        :return: A dict view of the account to be saved as json
        """
        data_communities = []
        for c in self.communities:
            data_communities.append(c.jsonify())

        data_wallets = []
        for w in self.wallets:
            data_wallets.append(w.jsonify())

        data = {'name': self.name,
                'salt': self.salt,
                'pubkey': self.pubkey,
                'communities': data_communities,
                'wallets': data_wallets,
                'contacts': self.contacts,
                'file_version': __version__}
        return data
