"""
Created on 11 févr. 2014

@author: inso
"""

import logging
import time
import asyncio
from enum import Enum

from ucoinpy.documents.certification import SelfCertification
from ucoinpy.api import bma as bma
from ucoinpy.api.bma import PROTOCOL_VERSION

from ...tools.exceptions import Error, NoPeerAvailable,\
                                        MembershipNotFoundError, LookupFailureError
from PyQt5.QtCore import QObject, pyqtSignal


class LocalState(Enum):
    """
    The local state describes how the identity exists locally :
    COMPLETED means all its related datas (certifiers, certified...)
    were succefully downloaded
    PARTIAL means not all data are present locally
    NOT_FOUND means it could not be found anywhere
    """
    NOT_FOUND = 0
    PARTIAL = 1
    COMPLETED = 2


class BlockchainState(Enum):
    """
    The blockchain state describes how the identity
    was found :
    VALIDATED means it was found in the blockchain
    BUFFERED means it was found via a lookup but not in the
    blockchain
    NOT_FOUND means it could not be found anywhere
    """
    NOT_FOUND = 0
    BUFFERED = 1
    VALIDATED = 2


class Identity(QObject):
    """
    A person with a uid and a pubkey
    """
    def __init__(self, uid, pubkey, sigdate, local_state, blockchain_state):
        """
        Initializing a person object.

        :param str uid: The identity uid, also known as its uid on the network
        :param str pubkey: The identity pubkey
        :parma int sig_date: The date of signature of the self certification
        :param LocalState local_state: The local status of the identity
        :param BlockchainState blockchain_state: The blockchain status of the identity
        """
        super().__init__()
        self.uid = uid
        self.pubkey = pubkey
        self.sigdate = sigdate
        self.local_state = local_state
        self.blockchain_state = blockchain_state

    @classmethod
    def empty(cls, pubkey):
        return cls("", pubkey, None, LocalState.NOT_FOUND, BlockchainState.NOT_FOUND)

    @classmethod
    def from_handled_data(cls, uid, pubkey, sigdate, blockchain_state):
        return cls(uid, pubkey, sigdate, LocalState.COMPLETED, blockchain_state)

    @classmethod
    def from_json(cls, json_data):
        """
        Create a person from json data

        :param dict json_data: The person as a dict in json format
        :return: A new person if pubkey wasn't known, else a new person instance.
        """
        pubkey = json_data['pubkey']
        uid = json_data['uid']
        sigdate = json_data['sigdate']
        local_state = LocalState[json_data['local_state']]
        blockchain_state = BlockchainState[json_data['blockchain_state']]

        return cls(uid, pubkey, sigdate, local_state, blockchain_state)

    async def selfcert(self, community):
        """
        Get the identity self certification.
        This request is not cached in the person object.

        :param sakia.core.community.Community community: The community target to request the self certification
        :return: A SelfCertification ucoinpy object
        :rtype: ucoinpy.documents.certification.SelfCertification
        """
        try:
            timestamp = 0
            lookup_data = await community.bma_access.future_request(bma.wot.Lookup,
                                                                         req_args={'search': self.pubkey})

            for result in lookup_data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    for uid_data in uids:
                        # If we sigDate was written in the blockchain
                        if self.sigdate and uid_data["meta"]["timestamp"] == self.sigdate:
                                timestamp = uid_data["meta"]["timestamp"]
                                uid = uid_data["uid"]
                                signature = uid_data["self"]
                        # Else we choose the latest one found
                        elif uid_data["meta"]["timestamp"] > timestamp:
                            timestamp = uid_data["meta"]["timestamp"]
                            uid = uid_data["uid"]
                            signature = uid_data["self"]

                    if not self.sigdate:
                        self.sigdate = timestamp

                    return SelfCertification(PROTOCOL_VERSION,
                                             community.currency,
                                             self.pubkey,
                                             timestamp,
                                             uid,
                                             signature)
        except ValueError as e:
            if '404' in str(e):
                raise LookupFailureError(self.pubkey, community)
        except NoPeerAvailable:
            logging.debug("No peer available")

    async def get_join_date(self, community):
        """
        Get the person join date.
        This request is not cached in the person object.

        :param sakia.core.community.Community community: The community target to request the join date
        :return: A datetime object
        """
        try:
            search = await community.bma_access.future_request(bma.blockchain.Membership,
                                                                    {'search': self.pubkey})
            if len(search['memberships']) > 0:
                membership_data = search['memberships'][0]
                block = await community.bma_access.future_request(bma.blockchain.Block,
                                req_args={'number': membership_data['blockNumber']})
                return block['medianTime']
        except ValueError as e:
            if '404' in str(e) or '400' in str(e):
                raise MembershipNotFoundError(self.pubkey, community.name)
        except NoPeerAvailable as e:
            logging.debug(str(e))
            raise MembershipNotFoundError(self.pubkey, community.name)

    async def get_expiration_date(self, community):
        try:
            membership = await self.membership(community)
            join_block_number = membership['blockNumber']
            try:
                join_block = await community.bma_access.future_request(bma.blockchain.Block,
                                req_args={'number': join_block_number})

                parameters = await community.bma_access.future_request(bma.blockchain.Parameters)
                join_date = join_block['medianTime']
                expiration_date = join_date + parameters['sigValidity']
            except NoPeerAvailable:
                expiration_date = None
            except ValueError as e:
                logging.debug("Expiration date not found")
                expiration_date = None
        except MembershipNotFoundError:
            expiration_date = None
        return expiration_date


#TODO: Manage 'OUT' memberships ? Maybe ?
    async def membership(self, community):
        """
        Get the person last membership document.

        :param sakia.core.community.Community community: The community target to request the join date
        :return: The membership data in BMA json format
        :rtype: dict
        """
        try:
            search = await community.bma_access.future_request(bma.blockchain.Membership,
                                           {'search': self.pubkey})
            block_number = -1
            membership_data = None
            #TODO: Should not be here, should be set when we look for the identity
            #We do it because we do not have this info in certifiers-of yet...
            self.sigdate = search['sigDate']
            for ms in search['memberships']:
                if ms['blockNumber'] > block_number:
                    block_number = ms['blockNumber']
                    if 'type' in ms:
                        if ms['type'] is 'IN':
                            membership_data = ms
                    else:
                        membership_data = ms
            if membership_data:
                return membership_data
            else:
                raise MembershipNotFoundError(self.pubkey, community.name)

        except ValueError as e:
            if '404' in str(e) or '400' in str(e):
                raise MembershipNotFoundError(self.pubkey, community.name)
        except NoPeerAvailable as e:
            logging.debug(str(e))
            raise MembershipNotFoundError(self.pubkey, community.name)

    async def published_uid(self, community):
        try:
            data = await community.bma_access.future_request(bma.wot.Lookup,
                                 req_args={'search': self.pubkey})
            timestamp = 0

            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    person_uid = ""
                    for uid_data in uids:
                        if uid_data["meta"]["timestamp"] > timestamp:
                            timestamp = uid_data["meta"]["timestamp"]
                            person_uid = uid_data["uid"]
                        if person_uid == self.uid:
                            return True
        except ValueError as e:
            if '404' in str(e):
                return False
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return False

    async def uid_is_revokable(self, community):
        published = await self.published_uid(community)
        if published:
            try:
                await community.bma_access.future_request(bma.wot.CertifiersOf,
                                                               {'search': self.pubkey})
            except ValueError as e:
                if '404' in str(e) or '400' in str(e):
                    return True
        return False

    async def is_member(self, community):
        """
        Check if the person is a member of a community

        :param sakia.core.community.Community community: The community target to request the join date
        :return: True if the person is a member of a community
        """
        try:
            certifiers = await community.bma_access.future_request(bma.wot.CertifiersOf,
                                                                        {'search': self.pubkey})
            return certifiers['isMember']
        except ValueError as e:
            if '404' in str(e) or '400' in str(e):
                pass
            else:
                raise
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return False

    async def certifiers_of(self, identities_registry, community):
        """
        Get the list of this person certifiers

        :param sakia.core.registry.identities.IdentitiesRegistry identities_registry: The identities registry
        :param sakia.core.community.Community community: The community target to request the join date
        :return: The list of the certifiers of this community
        :rtype: list
        """
        certifiers = list()
        try:
            data = await community.bma_access.future_request(bma.wot.CertifiersOf,
                                                                  {'search': self.pubkey})

            for certifier_data in data['certifications']:
                certifier = {}
                certifier['identity'] = identities_registry.from_handled_data(certifier_data['uid'],
                                                                              certifier_data['pubkey'],
                                                                              None,
                                                                              BlockchainState.VALIDATED,
                                                                              community)
                certifier['cert_time'] = certifier_data['cert_time']['medianTime']
                if 'written' in certifier_data and type(certifier_data['written']) is dict:
                    certifier['block_number'] = certifier_data['written']['number']
                else:
                    certifier['block_number'] = certifier_data['cert_time']['block']

                certifiers.append(certifier)
        except ValueError as e:
            if '404' in str(e):
                logging.debug('bma.wot.CertifiersOf request error: {0}'.format(str(e)))
            else:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))

        try:
            data = await community.bma_access.future_request(bma.wot.Lookup, {'search': self.pubkey})
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    self._refresh_uid(result['uids'])
                    for uid_data in result['uids']:
                        for certifier_data in uid_data['others']:
                            for uid in certifier_data['uids']:
                                # add a certifier
                                certifier = {}
                                certifier['identity'] = identities_registry.\
                                    from_handled_data(uid,
                                                      certifier_data['pubkey'],
                                                      None,
                                                      BlockchainState.BUFFERED,
                                                      community)
                                block = await community.bma_access.future_request(bma.blockchain.Block,
                                                                     {'number': certifier_data['meta']['block_number']})
                                certifier['cert_time'] = block['medianTime']
                                certifier['block_number'] = None

                                certifiers.append(certifier)
        except ValueError as e:
            logging.debug("Lookup error : {0}".format(str(e)))
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return certifiers

    async def unique_valid_certifiers_of(self, identities_registry, community):
        """
        Get the certifications in the blockchain and in the pools
        Get only unique and last certification for each pubkey
        :param sakia.core.registry.identities.IdentitiesRegistry identities_registry: The identities registry
        :param sakia.core.community.Community community: The community target to request the join date
        :return: The list of the certifiers of this community
        :rtype: list
        """
        certifier_list = await self.certifiers_of(identities_registry, community)
        unique_valid = []
        #  add certifiers of uid
        for certifier in tuple(certifier_list):
            # add only valid certification...
            try:
                cert_expired = await community.certification_expired(certifier['cert_time'])
            except NoPeerAvailable:
                logging.debug("No peer available")
                cert_expired = True

            if not cert_expired:
                # keep only the latest certification
                already_found = [c['identity'].pubkey for c in unique_valid]
                if certifier['identity'].pubkey in already_found:
                    index = already_found.index(certifier['identity'].pubkey)
                    if certifier['cert_time'] > unique_valid[index]['cert_time']:
                        unique_valid[index] = certifier
                else:
                    unique_valid.append(certifier)
        return unique_valid

    async def certified_by(self, identities_registry, community):
        """
        Get the list of persons certified by this person
        :param sakia.core.registry.IdentitiesRegistry identities_registry: The registry
        :param sakia.core.Community community: The community

        :param sakia.core.community.Community community: The community target to request the join date
        :return: The list of the certified persons of this community in BMA json format
        :rtype: list
        """
        certified_list = list()
        try:
            data = await community.bma_access.future_request(bma.wot.CertifiedBy, {'search': self.pubkey})
            for certified_data in data['certifications']:
                certified = {}
                certified['identity'] = identities_registry.from_handled_data(certified_data['uid'],
                                                                              certified_data['pubkey'],
                                                                              None,
                                                                              BlockchainState.VALIDATED,
                                                                              community)
                certified['cert_time'] = certified_data['cert_time']['medianTime']
                if 'written' in certified_data and type(certified_data['written']) is dict:
                    certified['block_number'] = certified_data['written']['number']
                else:
                    certified['block_number'] = certified_data['cert_time']['block']
                certified_list.append(certified)
        except ValueError as e:
            if '404' in str(e):
                logging.debug('bma.wot.CertifiersOf request error')
        except NoPeerAvailable as e:
            logging.debug(str(e))

        try:
            data = await community.bma_access.future_request(bma.wot.Lookup, {'search': self.pubkey})
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    self._refresh_uid(result['uids'])
                    for certified_data in result['signed']:
                        certified = {}
                        certified['identity'] = identities_registry.from_handled_data(certified_data['uid'],
                                                                          certified_data['pubkey'],
                                                                          None,
                                                                          BlockchainState.BUFFERED,
                                                                          community)
                        certified['cert_time'] = certified_data['meta']['timestamp']
                        certified['block_number'] = None
                        certified_list.append(certified)
        except ValueError as e:
            if '404' in str(e):
                logging.debug('bma.wot.Lookup request error')
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return certified_list

    async def unique_valid_certified_by(self, identities_registry, community):
        certified_list = await self.certified_by(identities_registry, community)
        unique_valid = []
        #  add certifiers of uid
        for certified in tuple(certified_list):
            # add only valid certification...
            try:
                cert_expired = await community.certification_expired(certified['cert_time'])
            except NoPeerAvailable:
                logging.debug("No peer available")
                cert_expired = True

            if not cert_expired:
                # keep only the latest certification
                already_found = [c['identity'].pubkey for c in unique_valid]
                if certified['identity'].pubkey in already_found:
                    index = already_found.index(certified['identity'].pubkey)
                    if certified['cert_time'] > unique_valid[index]['cert_time']:
                        unique_valid[index] = certified
                else:
                    unique_valid.append(certified)
        return unique_valid

    async def membership_expiration_time(self, community):
        membership = await self.membership(community)
        join_block = membership['blockNumber']
        block = await community.get_block(join_block)
        join_date = block['medianTime']
        parameters = await community.parameters()
        expiration_date = join_date + parameters['sigValidity']
        current_time = time.time()
        return expiration_date - current_time

    def _refresh_uid(self, uids):
        """
        Refresh UID from uids list, got from a successful lookup request
        :param list uids: UIDs got from a lookup request
        """
        timestamp = 0
        if self.local_state == LocalState.NOT_FOUND:
            for uid_data in uids:
                if uid_data["meta"]["timestamp"] > timestamp:
                    timestamp = uid_data["meta"]["timestamp"]
                    identity_uid = uid_data["uid"]
                    self.uid = identity_uid
                    self.blockchain_state = BlockchainState.BUFFERED
                    self.local_state = LocalState.PARTIAL

    def jsonify(self):
        """
        Get the community as dict in json format.
        :return: The community as a dict in json format
        """
        data = {'uid': self.uid,
                'pubkey': self.pubkey,
                'sigdate': self.sigdate,
                'local_state': self.local_state.name,
                'blockchain_state': self.blockchain_state.name}
        return data

    def __str__(self):
        return "{uid} - {pubkey} - {sigdate} - {local} - {blockchain}".format(uid=self.uid,
                                                                            pubkey=self.pubkey,
                                                                            sigdate=self.sigdate,
                                                                            local=self.local_state,
                                                                            blockchain=self.blockchain_state)
