"""
Created on 1 févr. 2014

@author: inso
"""

from ucoinpy.documents.certification import SelfCertification, Certification, Revocation
from ucoinpy.documents.membership import Membership
from ucoinpy.key import SigningKey

import logging
import time
import asyncio

from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication
from PyQt5.QtNetwork import QNetworkReply

from . import money
from .wallet import Wallet
from .community import Community
from .registry import LocalState
from ..tools.exceptions import ContactAlreadyExists
from ..tools.decorators import asyncify
from ..core.net.api import bma as qtbma
from ..core.net.api.bma import PROTOCOL_VERSION


class Account(QObject):
    """
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    """
    loading_progressed = pyqtSignal(int, int)
    loading_finished = pyqtSignal(list)
    wallets_changed = pyqtSignal()
    membership_broadcasted = pyqtSignal()
    certification_broadcasted = pyqtSignal()
    selfcert_broadcasted = pyqtSignal()
    revoke_broadcasted = pyqtSignal()
    broadcast_error = pyqtSignal(int, str)

    def __init__(self, salt, pubkey, name, communities, wallets, contacts, identities_registry):
        """
        Create an account

        :param str salt: The root key salt
        :param str pubkey: Known account pubkey. Used to check that password \
         is OK by comparing (salt, given_passwd) = (pubkey, privkey) \
         with known pubkey
        :param str name: The account name, same as network identity uid
        :param list of cutecoin.core.Community communities: Community objects referenced by this account
        :param list of cutecoin.core.Wallet wallets: Wallet objects owned by this account
        :param list of dict contacts: Contacts of this account
        :param cutecoin.core.registry.IdentitiesRegistry: The identities registry intance

        .. warnings:: The class methods create and load should be used to create an account
        """
        super().__init__()
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts
        self._refreshing = False
        self._identities_registry = identities_registry
        self._current_ref = 0

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
    def load(cls, json_data, network_manager, identities_registry):
        """
        Factory method to create an Account object from its json view.
        :rtype : cutecoin.core.account.Account
        :param dict json_data: The account view as a json dict
        :param PyQt5.QtNetwork import QNetworkManager: network_manager
        :param cutecoin.core.registry.self._identities_registry: identities_registry
        :return: A new account object created from the json datas
        """
        salt = json_data['salt']
        pubkey = json_data['pubkey']

        name = json_data['name']
        contacts = []

        for contact_data in json_data['contacts']:
            contacts.append(contact_data)

        wallets = []
        for data in json_data['wallets']:
            wallets.append(Wallet.load(data, identities_registry))

        communities = []
        for data in json_data['communities']:
            community = Community.load(network_manager, data)
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
        if not self._refreshing:
            self._refreshing = True
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
                self.loading_progressed.emit(account_value, account_max)

            def wallet_finished(received):
                logging.debug("Finished loading wallet")
                nonlocal loaded_wallets
                loaded_wallets += 1
                if loaded_wallets == len(self.wallets):
                    logging.debug("All wallets loaded")
                    self._refreshing = False
                    self.loading_finished.emit(received_list)
                    for w in self.wallets:
                        w.refresh_progressed.disconnect(progressing)
                        w.refresh_finished.disconnect(wallet_finished)

            for w in self.wallets:
                w.refresh_progressed.connect(progressing)
                w.refresh_finished.connect(wallet_finished)
                w.init_cache(app, community)
                w.refresh_transactions(community, received_list)

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

    @asyncio.coroutine
    def identity(self, community):
        """
        Get the account identity in the specified community
        :param cutecoin.core.community.Community community: The community where to look after the identity
        :return: The account identity in the community
        :rtype: cutecoin.core.registry.Identity
        """
        identity = yield from self._identities_registry.future_find(self.pubkey, community)
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

    @asyncio.coroutine
    def future_amount(self, community):
        """
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        """
        value = 0
        for w in self.wallets:
            val = yield from w.future_value(community)
            value += val
        return value

    @asyncio.coroutine
    def amount(self, community):
        """
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        """
        value = 0
        for w in self.wallets:
            val = yield from w.value(community)
            value += val
        return value

    @asyncio.coroutine
    def send_selfcert(self, password, community):
        """
        Send our self certification to a target community

        :param str password: The account SigningKey password
        :param community: The community target of the self certification
        """
        selfcert = SelfCertification(PROTOCOL_VERSION,
                                     community.currency,
                                     self.pubkey,
                                     int(time.time()),
                                     self.name,
                                     None)
        key = SigningKey(self.salt, password)
        selfcert.sign([key])
        logging.debug("Key publish : {0}".format(selfcert.signed_raw()))
        replies = community.bma_access.broadcast(qtbma.wot.Add, {}, {'pubkey': self.pubkey,
                                              'self_': selfcert.signed_raw(),
                                              'other': ""})
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_selfcert_replies(replies, reply))

    def __handle_selfcert_replies(self, replies, reply):
        """
        Handle the reply, if the request was accepted, disconnect
        all other replies

        :param QNetworkReply reply: The reply of this handler
        :param list of QNetworkReply replies: All request replies
        :return:
        """
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
                    else:
                        raise
            self.selfcert_broadcasted.emit()
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    @asyncio.coroutine
    def send_membership(self, password, community, mstype):
        """
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param str password: The account SigningKey password
        :param community: The community target of the membership document
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        """
        logging.debug("Send membership")

        blockid = yield from community.blockid()
        self_identity = yield from self._identities_registry.future_find(self.pubkey, community)
        selfcert = yield from self_identity.selfcert(community)

        membership = Membership(PROTOCOL_VERSION, community.currency,
                                selfcert.pubkey, blockid['number'],
                                blockid['hash'], mstype, selfcert.uid,
                                selfcert.timestamp, None)
        key = SigningKey(self.salt, password)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        replies = community.bma_access.broadcast(qtbma.blockchain.Membership, {},
                            {'membership': membership.signed_raw()})
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_membership_replies(replies, reply))

    def __handle_membership_replies(self, replies, reply):
        """
        Handle the reply, if the request was accepted, disconnect
        all other replies

        :param QNetworkReply reply: The reply of this handler
        :param list of QNetworkReply replies: All request replies
        :return:
        """
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
                    else:
                        raise
            self.membership_broadcasted.emit()
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    @asyncio.coroutine
    def certify(self, password, community, pubkey):
        """
        Certify an other identity

        :param str password: The account SigningKey password
        :param cutecoin.core.community.Community community: The community target of the certification
        :param str pubkey: The certified identity pubkey
        """
        logging.debug("Certdata")
        blockid = yield from community.blockid()
        identity = yield from self._identities_registry.future_find(pubkey, community)
        selfcert = yield from identity.selfcert(community)
        certification = Certification(PROTOCOL_VERSION, community.currency,
                                      self.pubkey, pubkey,
                                      blockid['number'], blockid['hash'], None)

        key = SigningKey(self.salt, password)
        certification.sign(selfcert, [key])
        signed_cert = certification.signed_raw(selfcert)
        logging.debug("Certification : {0}".format(signed_cert))

        data = {'pubkey': pubkey,
                'self_': selfcert.signed_raw(),
                'other': "{0}\n".format(certification.inline())}
        logging.debug("Posted data : {0}".format(data))
        replies = community.bma_access.broadcast(qtbma.wot.Add, {}, data)
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_certification_reply(replies, reply))

    def __handle_certification_reply(self, replies, reply):
        """
        Handle the reply, if the request was accepted, disconnect
        all other replies

        :param QNetworkReply reply: The reply of this handler
        :param list of QNetworkReply replies: All request replies
        :return:
        """
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
                    else:
                        raise
            self.certification_broadcasted.emit()
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    @asyncio.coroutine
    def revoke(self, password, community):
        """
        Revoke self-identity on server, not in blockchain

        :param str password: The account SigningKey password
        :param cutecoin.core.community.Community community: The community target of the revocation
        """
        revoked = yield from self._identities_registry.future_find(self.pubkey, community)

        revocation = Revocation(PROTOCOL_VERSION, community.currency, None)
        selfcert = revoked.selfcert(community)

        key = SigningKey(self.salt, password)
        revocation.sign(selfcert, [key])

        logging.debug("Self-Revocation Document : \n{0}".format(revocation.raw(selfcert)))
        logging.debug("Signature : \n{0}".format(revocation.signatures[0]))

        data = {
            'pubkey': revoked.pubkey,
            'self_': selfcert.signed_raw(),
            'sig': revocation.signatures[0]
        }
        logging.debug("Posted data : {0}".format(data))
        replies = community.broadcast(qtbma.wot.Revoke, {}, data)
        for r in replies:
            r.finished.connect(lambda reply=r: self.__handle_certification_reply(replies, reply))

    def __handle_revoke_reply(self, replies, reply):
        """
        Handle the reply, if the request was accepted, disconnect
        all other replies

        :param QNetworkReply reply: The reply of this handler
        :param list of QNetworkReply replies: All request replies
        :return:
        """
        strdata = bytes(reply.readAll()).decode('utf-8')
        logging.debug("Received reply : {0} : {1}".format(reply.error(), strdata))
        if reply.error() == QNetworkReply.NoError:
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
                    else:
                        raise
            self.revoke_broadcasted.emit()
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    def start_coroutines(self):
        for c in self.communities:
            c.start_coroutines()

    def stop_coroutines(self):
        for c in self.communities:
            c.stop_coroutines()

        for w in self.wallets:
            w.stop_coroutines()

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
                'contacts': self.contacts}
        return data
