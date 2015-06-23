"""
Created on 1 févr. 2014

@author: inso
"""

from ucoinpy.documents.certification import SelfCertification, Certification, Revocation
from ucoinpy.documents.membership import Membership
from ucoinpy.key import SigningKey

import logging
import time
import math
import json
import asyncio

from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication, QT_TRANSLATE_NOOP
from PyQt5.QtNetwork import QNetworkReply

from .wallet import Wallet
from .community import Community
from .registry import Identity, IdentitiesRegistry
from ..tools.exceptions import ContactAlreadyExists
from ..core.net.api import bma as qtbma
from ..core.net.api.bma import PROTOCOL_VERSION

def quantitative(units, community):
    """
    Return quantitative value of units

    :param int units:   Value
    :param cutecoin.core.community.Community community: Community instance
    :return: int
    """
    return int(units)


def relative(units, community):
    """
    Return relaive value of units

    :param int units:   Value
    :param cutecoin.core.community.Community community: Community instance
    :return: float
    """
    # calculate ud(t+1)
    ud_block = community.get_ud_block()
    if ud_block:
        ud = math.ceil(
            max(community.dividend(),
                float(0) if ud_block['membersCount'] == 0 else
                community.parameters['c'] * community.monetary_mass / ud_block['membersCount']))

        if ud == 0:
            return float(0)
        else:
            relative_value = units / float(ud)
            return relative_value
    else:
        return float(0)


def quantitative_zerosum(units, community):
    """
    Return quantitative value of units minus the average value

    :param int units:   Value
    :param cutecoin.core.community.Community community: Community instance
    :return: int
    """
    # fixme: the value "community.nb_members" is not up to date, luckyly the good value is in "community.get_ud_block()['membersCount']"
    average = community.monetary_mass / community.get_ud_block()['membersCount']
    return units - average


def relative_zerosum(units, community):
    """
    Return relative value of units minus the average value

    :param int units:   Value
    :param cutecoin.core.community.Community community: Community instance
    :return: float
    """
    # fixme: the value "community.nb_members" is not up to date, luckyly the good value is in "community.get_ud_block()['membersCount']"
    median = community.monetary_mass / community.nb_members
    # calculate ud(t+1)
    ud = math.ceil(
        max(community.dividend,
            community.parameters['c'] * community.monetary_mass / community.get_ud_block()['membersCount'])
    )
    relative_value = units / float(ud)
    relative_median = median / ud
    return relative_value - relative_median


class Account(QObject):
    """
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    """
    # referentials are defined here
    # it is a list of tupple, each tupple contains :
    # (
    #   function used to calculate value,
    #   format string to display value,
    #   function used to calculate on differential value,
    #   format string to display differential value,
    #   translated name of referential,
    #   type relative "r" or quantitative "q" to help choose precision on display
    # )
    referentials = (
        (quantitative, '{0}', quantitative, '{0}', QT_TRANSLATE_NOOP('Account', 'Units'), 'q'),
        (relative, QT_TRANSLATE_NOOP('Account', 'UD {0}'), relative, QT_TRANSLATE_NOOP('Account', 'UD {0}'),
         QT_TRANSLATE_NOOP('Account', 'UD'), 'r'),
        (quantitative_zerosum, QT_TRANSLATE_NOOP('Account', 'Q0 {0}'), quantitative, '{0}',
         QT_TRANSLATE_NOOP('Account', 'Quant Z-sum'), 'q'),
        (relative_zerosum, QT_TRANSLATE_NOOP('Account', 'R0 {0}'), relative, QT_TRANSLATE_NOOP('Account', 'UD {0}'),
         QT_TRANSLATE_NOOP('Account', 'Relat Z-sum'), 'r')
    )

    loading_progressed = pyqtSignal(int, int)
    loading_finished = pyqtSignal(list)
    inner_data_changed = pyqtSignal(str)
    wallets_changed = pyqtSignal()
    membership_broadcasted = pyqtSignal()
    certification_broadcasted = pyqtSignal()
    broadcast_error = pyqtSignal(int, str)

    def __init__(self, salt, pubkey, name, communities, wallets, contacts, identities_registry):
        '''
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
        '''
        super().__init__()
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts
        self._identities_registry = identities_registry
        self.referential = 0

    @classmethod
    def create(cls, name, identities_registry):
        '''
        Factory method to create an empty account object
        This new account doesn't have any key and it should be given
        one later
        It doesn't have any community nor does it have wallets.
        Communities could be added later, wallets will be managed
        by its wallet pool size.

        :param str name: The account name, same as network identity uid
        :return: A new empty account object
        '''
        account = cls(None, None, name, [], [], [], identities_registry)
        return account

    @classmethod
    def load(cls, json_data, network_manager, identities_registry):
        '''
        Factory method to create an Account object from its json view.
        :rtype : cutecoin.core.account.Account
        :param dict json_data: The account view as a json dict
        :param PyQt5.QtNetwork import QNetworkManager: network_manager
        :param cutecoin.core.registry.self._identities_registry: identities_registry
        :return: A new account object created from the json datas
        '''
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
        '''
        :return: True if account.pubkey == other.pubkey
        '''
        if other is not None:
            return other.pubkey == self.pubkey
        else:
            return False

    def check_password(self, password):
        '''
        Method to verify the key password validity

        :param str password: The key password
        :return: True if the generated pubkey is the same as the account
        .. warnings:: Generates a new temporary SigningKey
        '''
        key = SigningKey(self.salt, password)
        return (key.pubkey == self.pubkey)

    def add_contact(self, new_contact):
        same_contact = [contact for contact in self.contacts
                        if new_contact['pubkey'] == contact['pubkey']]

        if len(same_contact) > 0:
            raise ContactAlreadyExists(new_contact['name'], same_contact[0]['name'])
        self.contacts.append(new_contact)

    def add_community(self, community):
        '''
        Add a community to the account

        :param community: A community object to add
        '''
        self.communities.append(community)
        return community

    def refresh_transactions(self, community):
        """
        Refresh the local account cache
        This needs n_wallets * n_communities cache refreshing to end

        .. note:: emit the Account pyqtSignal loading_progressed during refresh
        """
        loaded_wallets = 0
        received_list = []

        def progressing(value, maximum):
            account_value = maximum * loaded_wallets + value
            account_max = maximum  * len(self.wallets)
            self.loading_progressed.emit(account_value, account_max)

        for w in self.wallets:
            w.refresh_progressed.connect(progressing)
            QCoreApplication.processEvents()
            w.init_cache(community)
            w.refresh_transactions(community, received_list)
            loaded_wallets += 1
            QCoreApplication.processEvents()
        self.loading_finished.emit(received_list)

    def set_display_referential(self, index):
        self.referential = index

    def identity(self, community):
        """
        Get the account identity in the specified community
        :param cutecoin.core.community.Community community: The community where to look after the identity
        :return: The account identity in the community
        :rtype: cutecoin.core.registry.Identity
        """
        identity = self._identities_registry.lookup(self.pubkey, community)
        if identity.status == Identity.NOT_FOUND:
            identity.uid = self.name
        return identity

    @property
    def units_to_ref(self):
        return Account.referentials[self.referential][0]

    @property
    def units_to_diff_ref(self):
        return Account.referentials[self.referential][2]

    def ref_name(self, currency):
        text = QCoreApplication.translate('Account',
                                          Account.referentials[self.referential][1])
        return text.format(currency)

    def diff_ref_name(self, currency):
        text = QCoreApplication.translate('Account', Account.referentials[self.referential][3])
        return text.format(currency)

    def ref_type(self):
        """
        Return type of referential ('q' or 'r', for quantitative or relative)
        :return: str
        """
        return Account.referentials[self.referential][5]

    def set_walletpool_size(self, size, password):
        '''
        Change the size of the wallet pool

        :param int size: The new size of the wallet pool
        :param str password: The password of the account, same for all wallets
        '''
        logging.debug("Defining wallet pool size")
        if len(self.wallets) < size:
            for i in range(len(self.wallets), size):
                wallet = Wallet.create(i, self.salt, password,
                                       "Wallet {0}".format(i), self._identities_registry)
                self.wallets.append(wallet)
        else:
            self.wallets = self.wallets[:size]
        self.wallets_changed.emit()

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
        identity = yield from self._identities_registry.future_lookup(pubkey, community)
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
        return True

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
            self.certification_broadcasted.emit()
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    def revoke(self, password, community):
        """
        Revoke self-identity on server, not in blockchain

        :param str password: The account SigningKey password
        :param cutecoin.core.community.Community community: The community target of the revocation
        """
        revoked = self._identities_registry.lookup(self.pubkey, community)

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
        community.broadcast(qtbma.wot.Revoke, {}, data)

    def transfers(self, community):
        '''
        Get all transfers done in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: All account wallets transfers
        '''
        sent = []
        for w in self.wallets:
            sent.extend(w.transfers(community))
        return sent

    @asyncio.coroutine
    def future_amount(self, community):
        '''
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        '''
        value = 0
        for w in self.wallets:
            val = yield from w.future_value(community)
            value += val
        return value

    def amount(self, community):
        '''
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        '''
        value = 0
        for w in self.wallets:
            val = w.value(community)
            value += val
        return value

    def send_selfcert(self, password, community):
        '''
        Send our self certification to a target community

        :param str password: The account SigningKey password
        :param community: The community target of the self certification
        '''
        selfcert = SelfCertification(PROTOCOL_VERSION,
                                     community.currency,
                                     self.pubkey,
                                     int(time.time()),
                                     self.name,
                                     None)
        key = SigningKey(self.salt, password)
        selfcert.sign([key])
        logging.debug("Key publish : {0}".format(selfcert.signed_raw()))
        community.broadcast(qtbma.wot.Add, {}, {'pubkey': self.pubkey,
                                              'self_': selfcert.signed_raw(),
                                              'other': []})

    @asyncio.coroutine
    def send_membership(self, password, community, mstype):
        '''
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param str password: The account SigningKey password
        :param community: The community target of the membership document
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        '''
        logging.debug("Send membership")

        blockid = yield from community.blockid()
        self_identity = yield from self._identities_registry.future_lookup(self.pubkey, community)
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
            self.membership_broadcasted.emit()
            for r in replies:
                try:
                    r.disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        logging.debug("Could not disconnect a reply")
        else:
            for r in replies:
                if not r.isFinished() or r.error() == QNetworkReply.NoError:
                    return
            self.broadcast_error.emit(r.error(), strdata)

    def jsonify(self):
        '''
        Get the account in a json format.

        :return: A dict view of the account to be saved as json
        '''
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
