"""
Created on 1 févr. 2014

@author: inso
"""

from duniterpy.documents import Membership, SelfCertification, Certification, Revocation, BlockUID, Block
from duniterpy.key import SigningKey, ScryptParams
from duniterpy.api import bma
from duniterpy.api.bma import PROTOCOL_VERSION
from duniterpy.api import errors

import logging
import asyncio
from pkg_resources import parse_version
from aiohttp.errors import ClientError
from PyQt5.QtCore import QObject, pyqtSignal

from . import money
from .wallet import Wallet
from .community import Community
from .registry import LocalState
from ..tools.exceptions import ContactAlreadyExists, LookupFailureError
from .. import __version__


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

    def __init__(self, salt, pubkey, scrypt_params, name, communities, wallets, contacts, identities_registry):
        """
        Create an account

        :param str salt: The root key salt
        :param str pubkey: Known account pubkey. Used to check that password \
         is OK by comparing (salt, given_passwd) = (pubkey, privkey) \
         with known pubkey
        :param duniterpy.key.ScryptParams scrypt_params: the scrypt params of the key
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
        self.scrypt_params = scrypt_params
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
        account = cls(None, None, None, name, [], [], [], identities_registry)
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

        if file_version <= parse_version('0.20.11'):
            scrypt_params = ScryptParams(4096, 16, 1)
        else:
            scrypt_params = ScryptParams(json_data['scrypt_params']['N'],
                                         json_data['scrypt_params']['r'],
                                         json_data['scrypt_params']['p'])

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

        account = cls(salt, pubkey, scrypt_params, name, communities, wallets,
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
        key = SigningKey(self.salt, password, self.scrypt_params)
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

    def set_scrypt_infos(self, salt, password, scrypt_params):
        """
        Change the size of the wallet pool
        :param int size: The new size of the wallet pool
        :param str password: The password of the account, same for all wallets
        :param duniterpy.key.ScryptParams scrypt_params: The scrypt parameters
        """
        self.salt = salt
        self.scrypt_params = scrypt_params
        self.pubkey = SigningKey(self.salt, password, scrypt_params).pubkey
        wallet = Wallet.create(0, self.salt, password, scrypt_params,
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

    async def check_registered(self, community):
        """
        Checks for the pubkey and the uid of an account in a community
        :param sakia.core.Community community: The community we check for registration
        :return: (True if found, local value, network value)
        """
        def _parse_uid_certifiers(data):
            return self.name == data['uid'], self.name, data['uid']

        def _parse_uid_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    for uid_data in uids:
                        if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                            timestamp = uid_data["meta"]["timestamp"]
                            found_uid = uid_data["uid"]
            return self.name == found_uid, self.name, found_uid

        def _parse_pubkey_certifiers(data):
            return self.pubkey == data['pubkey'], self.pubkey, data['pubkey']

        def _parse_pubkey_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            found_result = ["", ""]
            for result in data['results']:
                uids = result['uids']
                for uid_data in uids:
                    if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                        timestamp = uid_data["meta"]["timestamp"]
                        found_uid = uid_data["uid"]
                if found_uid == self.name:
                    found_result = result['pubkey'], found_uid
            if found_result[1] == self.name:
                return self.pubkey == found_result[0], self.pubkey, found_result[0]
            else:
                return False, self.pubkey, None

        async def execute_requests(parsers, search):
            tries = 0
            request = bma.wot.CertifiersOf
            nonlocal registered
            #TODO: The algorithm is quite dirty
            #Multiplying the tries without any reason...
            while tries < 3 and not registered[0] and not registered[2]:
                try:
                    data = await community.bma_access.simple_request(request,
                                                                          req_args={'search': search})
                    if data:
                        registered = parsers[request](data)
                    tries += 1
                except errors.DuniterError as e:
                    if e.ucode in (errors.NO_MEMBER_MATCHING_PUB_OR_UID,
                                   e.ucode == errors.NO_MATCHING_IDENTITY):
                        if request == bma.wot.CertifiersOf:
                            request = bma.wot.Lookup
                            tries = 0
                        else:
                            tries += 1
                    else:
                        tries += 1
                except asyncio.TimeoutError:
                    tries += 1
                except ClientError:
                    tries += 1

        registered = (False, self.name, None)
        # We execute search based on pubkey
        # And look for account UID
        uid_parsers = {
                    bma.wot.CertifiersOf: _parse_uid_certifiers,
                    bma.wot.Lookup: _parse_uid_lookup
                   }
        await execute_requests(uid_parsers, self.pubkey)

        # If the uid wasn't found when looking for the pubkey
        # We look for the uid and check for the pubkey
        if not registered[0] and not registered[2]:
            pubkey_parsers = {
                        bma.wot.CertifiersOf: _parse_pubkey_certifiers,
                        bma.wot.Lookup: _parse_pubkey_lookup
                       }
            await execute_requests(pubkey_parsers, self.name)

        return registered

    async def send_selfcert(self, password, community):
        """
        Send our self certification to a target community

        :param str password: The account SigningKey password
        :param community: The community target of the self certification
        """
        try:
            block_data = await community.bma_access.simple_request(bma.blockchain.Current)
            signed_raw = "{0}{1}\n".format(block_data['raw'], block_data['signature'])
            block_uid = Block.from_signed_raw(signed_raw).blockUID
        except errors.DuniterError as e:
            if e.ucode == errors.NO_CURRENT_BLOCK:
                block_uid = BlockUID.empty()
            else:
                raise
        selfcert = SelfCertification(PROTOCOL_VERSION,
                                     community.currency,
                                     self.pubkey,
                                     self.name,
                                     block_uid,
                                     None)
        key = SigningKey(self.salt, password, self.scrypt_params)
        selfcert.sign([key])
        logging.debug("Key publish : {0}".format(selfcert.signed_raw()))

        responses = await community.bma_access.broadcast(bma.wot.Add, {}, {'identity': selfcert.signed_raw()})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        if result[0]:
            (await self.identity(community)).sigdate = block_uid
        return result

    async def send_membership(self, password, community, mstype):
        """
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param str password: The account SigningKey password
        :param community: The community target of the membership document
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        """
        logging.debug("Send membership")

        blockUID = community.network.current_blockUID
        self_identity = await self._identities_registry.future_find(self.pubkey, community)
        selfcert = await self_identity.selfcert(community)

        membership = Membership(PROTOCOL_VERSION, community.currency,
                                selfcert.pubkey, blockUID, mstype, selfcert.uid,
                                selfcert.timestamp, None)
        key = SigningKey(self.salt, password, self.scrypt_params)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        responses = await community.bma_access.broadcast(bma.blockchain.Membership, {},
                        {'membership': membership.signed_raw()})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def certify(self, password, community, pubkey):
        """
        Certify an other identity

        :param str password: The account SigningKey password
        :param sakia.core.community.Community community: The community target of the certification
        :param str pubkey: The certified identity pubkey
        """
        logging.debug("Certdata")
        blockUID = community.network.current_blockUID
        try:
            identity = await self._identities_registry.future_find(pubkey, community)
            selfcert = await identity.selfcert(community)
        except LookupFailureError as e:
            return False, str(e)

        if selfcert:
            certification = Certification(PROTOCOL_VERSION, community.currency,
                                          self.pubkey, pubkey, blockUID, None)

            key = SigningKey(self.salt, password, self.scrypt_params)
            certification.sign(selfcert, [key])
            signed_cert = certification.signed_raw(selfcert)
            logging.debug("Certification : {0}".format(signed_cert))

            data = {'cert': certification.signed_raw(selfcert)}
            logging.debug("Posted data : {0}".format(data))
            responses = await community.bma_access.broadcast(bma.wot.Certify, {}, data)
            result = (False, "")
            for r in responses:
                if r.status == 200:
                    result = (True, (await r.json()))
                    # signal certification to all listeners
                    self.certification_accepted.emit()
                elif not result[0]:
                    result = (False, (await r.text()))
                else:
                    await r.release()
            return result
        else:
            return False, self.tr("Could not find user self certification.")

    async def revoke(self, password, community):
        """
        Revoke self-identity on server, not in blockchain

        :param str password: The account SigningKey password
        :param sakia.core.community.Community community: The community target of the revokation
        """
        revoked = await self._identities_registry.future_find(self.pubkey, community)

        revokation = Revocation(PROTOCOL_VERSION, community.currency, None)
        selfcert = await revoked.selfcert(community)

        key = SigningKey(self.salt, password, self.scrypt_params)
        revokation.sign(selfcert, [key])

        logging.debug("Self-Revokation Document : \n{0}".format(revokation.raw(selfcert)))
        logging.debug("Signature : \n{0}".format(revokation.signatures[0]))

        data = {
            'pubkey': revoked.pubkey,
            'self_': selfcert.signed_raw(),
            'sig': revokation.signatures[0]
        }
        logging.debug("Posted data : {0}".format(data))
        responses = await community.bma_access.broadcast(bma.wot.Revoke, {}, data)
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def generate_revokation(self, community, password):
        """
        Generate account revokation document for given community
        :param sakia.core.Community community: the community
        :param str password: the password
        :return: the revokation document
        :rtype: duniterpy.documents.certification.Revocation
        """
        document = Revocation(PROTOCOL_VERSION, community.currency, self.pubkey, "")
        identity = await self.identity(community)
        selfcert = await identity.selfcert(community)

        key = SigningKey(self.salt, password, self.scrypt_params)

        document.sign(selfcert, [key])
        return document.signed_raw(selfcert)

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
                'scrypt_params': {
                    'N': self.scrypt_params.N,
                    'r': self.scrypt_params.N,
                    'p': self.scrypt_params.N,
                },
                'communities': data_communities,
                'wallets': data_wallets,
                'contacts': self.contacts,
                'file_version': __version__}
        return data
