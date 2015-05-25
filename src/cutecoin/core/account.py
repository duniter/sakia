'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy import PROTOCOL_VERSION
from ucoinpy.api import bma
from ucoinpy.documents.certification import SelfCertification, Certification, Revocation
from ucoinpy.documents.membership import Membership
from ucoinpy.key import SigningKey

import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication, QT_TRANSLATE_NOOP

from .wallet import Wallet
from .community import Community
from .person import Person
from ..tools.exceptions import ContactAlreadyExists


def quantitative(units, community):
    return int(units)


def relative(units, community):
    ud = community.dividend
    relative_value = units / float(ud)
    return relative_value


def quantitative_zerosum(units, community):
    median = community.monetary_mass / community.nb_members
    return units - median


def relative_zerosum(units, community):
    median = community.monetary_mass / community.nb_members
    ud = community.dividend
    relative_value = units / float(ud)
    relative_median = median / ud
    return relative_value - relative_median


class Account(QObject):

    '''
    An account is specific to a key.
    Each account has only one key, and a key can
    be locally referenced by only one account.
    '''
    referentials = {'Units': (quantitative, '{0}',
                              quantitative, '{0}'),
                    'UD': (relative, QT_TRANSLATE_NOOP('Account', 'ud {0}'),
                           relative, QT_TRANSLATE_NOOP('Account', 'ud {0}')),
                    'Quant Z-sum': (quantitative_zerosum,
                                    QT_TRANSLATE_NOOP('Account', 'q0 {0}'),
                                    quantitative, '{0}'),
                    'Relat Z-sum': (relative_zerosum,
                                    QT_TRANSLATE_NOOP('Account', 'r0 {0}'),
                                    relative,
                                    QT_TRANSLATE_NOOP('Account', 'ud {0}'))
                    }

    loading_progressed = pyqtSignal(int, int)

    def __init__(self, salt, pubkey, name, communities, wallets, contacts):
        '''
        Create an account

        :param str salt: The root key salt
        :param str pubkey: Known account pubkey. Used to check that password \
         is OK by comparing (salt, given_passwd) = (pubkey, privkey) \
         with known pubkey
        :param str name: The account name, same as network identity uid
        :param array communities: Community objects referenced by this account
        :param array wallets: Wallet objects owned by this account
        :param array contacts: Contacts of this account

        .. warnings:: The class methods create and load should be used to create an account
        '''
        super().__init__()
        self.salt = salt
        self.pubkey = pubkey
        self.name = name
        self.communities = communities
        self.wallets = wallets
        self.contacts = contacts
        self.referential = 'Units'

    @classmethod
    def create(cls, name):
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
        account = cls(None, None, name, [], [], [])
        return account

    @classmethod
    def load(cls, json_data):
        '''
        Factory method to create an Account object from its json view.
        :param dict json_data: The account view as a json dict
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
            wallets.append(Wallet.load(data))

        communities = []
        for data in json_data['communities']:
            community = Community.load(data)
            communities.append(community)

        account = cls(salt, pubkey, name, communities, wallets,
                      contacts)
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

    def refresh_cache(self):
        '''
        Refresh the local account cache
        This needs n_wallets * n_communities cache refreshing to end

        .. note:: emit the Account pyqtSignal loading_progressed during refresh
        '''
        loaded_wallets = 0

        def progressing(value, maximum):
            account_value = maximum * len(self.communities) * loaded_wallets + value
            account_max = maximum * len(self.communities) * len(self.wallets)
            self.loading_progressed.emit(account_value, account_max)

        for w in self.wallets:
            w.refresh_progressed.connect(progressing)
            QCoreApplication.processEvents()
            for c in self.communities:
                w.init_cache(c)
                loaded_wallets = loaded_wallets + 1
                QCoreApplication.processEvents()

    def set_display_referential(self, index):
        self.referential = index

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
                                       "Wallet {0}".format(i))
                self.wallets.append(wallet)
        else:
            self.wallets = self.wallets[:size]

    def certify(self, password, community, pubkey):
        """
        Certify an other identity

        :param str password: The account SigningKey password
        :param cutecoin.core.community.Community community: The community target of the certification
        :param str pubkey: The certified identity pubkey
        """
        certified = Person.lookup(pubkey, community)
        blockid = community.current_blockid()

        certification = Certification(PROTOCOL_VERSION, community.currency,
                                      self.pubkey, certified.pubkey,
                                      blockid['number'], blockid['hash'], None)

        selfcert = certified.selfcert(community)
        logging.debug("SelfCertification : {0}".format(selfcert.raw()))

        key = SigningKey(self.salt, password)
        certification.sign(selfcert, [key])
        signed_cert = certification.signed_raw(selfcert)
        logging.debug("Certification : {0}".format(signed_cert))

        data = {'pubkey': certified.pubkey,
                        'self_': selfcert.signed_raw(),
                        'other': "{0}\n".format(certification.inline())}
        logging.debug("Posted data : {0}".format(data))
        community.broadcast(bma.wot.Add, {}, data)

    def revoke(self, password, community):
        """
        Revoke self-identity on server, not in blockchain

        :param str password: The account SigningKey password
        :param cutecoin.core.community.Community community: The community target of the revocation
        """
        revoked = Person.lookup(self.pubkey, community)

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
        community.broadcast(bma.wot.Revoke, {}, data)

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

    def amount(self, community):
        '''
        Get amount of money owned in a community by all the wallets
        owned by this account

        :param community: The target community of this request
        :return: The value of all wallets values accumulated
        '''
        value = 0
        for w in self.wallets:
            value += w.value(community)
        return value

    def published_uid(self, community):
        '''
        Check if this account identity is a member of a community

        :param community: The target community of this request
        :return: True if the account is a member of the target community
        '''
        self_person = Person.lookup(self.pubkey, community)
        return self_person.published_uid(community)

    def member_of(self, community):
        '''
        Check if this account identity is a member of a community

        :param community: The target community of this request
        :return: True if the account is a member of the target community
        '''
        self_person = Person.lookup(self.pubkey, community)
        logging.debug("Self person : {0}".format(self_person.uid))
        return self_person.is_member(community)

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
        community.broadcast(bma.wot.Add, {}, {'pubkey': self.pubkey,
                                    'self_': selfcert.signed_raw(),
                                    'other': []})

    def send_membership(self, password, community, mstype):
        '''
        Send a membership document to a target community

        :param str password: The account SigningKey password
        :param community: The community target of the membership document
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        '''
        self_ = Person.lookup(self.pubkey, community)
        selfcert = self_.selfcert(community)

        blockid = community.current_blockid()

        membership = Membership(PROTOCOL_VERSION, community.currency,
                          selfcert.pubkey, blockid['number'],
                          blockid['hash'], mstype, selfcert.uid,
                          selfcert.timestamp, None)
        key = SigningKey(self.salt, password)
        membership.sign([key])
        logging.debug("Membership : {0}".format(membership.signed_raw()))
        community.broadcast(bma.blockchain.Membership, {},
                       {'membership': membership.signed_raw()})

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

    def get_person(self):
        return Person.from_metadata({'text': self.name,
                                     'id': self.pubkey})
