"""
Created on 11 févr. 2014

@author: inso
"""

import logging
import time
import asyncio
from enum import Enum

from ucoinpy.documents.certification import SelfCertification
from cutecoin.tools.exceptions import Error, NoPeerAvailable,\
                                        MembershipNotFoundError
from cutecoin.core.net.api import bma as qtbma
from cutecoin.core.net.api.bma import PROTOCOL_VERSION
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
    inner_data_changed = pyqtSignal(str)

    def __init__(self, uid, pubkey, local_state, blockchain_state):
        """
        Initializing a person object.

        :param str uid: The person uid, also known as its uid on the network
        :param str pubkey: The person pubkey
        :param LocalState local_state: The local status of the identity
        :param BlockchainState blockchain_state: The blockchain status of the identity
        """
        super().__init__()
        self.uid = uid
        self.pubkey = pubkey
        self.local_state = local_state
        self.blockchain_state = blockchain_state

    @classmethod
    def empty(cls, pubkey):
        return cls("", pubkey, LocalState.NOT_FOUND, BlockchainState.NOT_FOUND)

    @classmethod
    def from_handled_data(cls, uid, pubkey, blockchain_state):
        return cls(uid, pubkey, LocalState.COMPLETED, blockchain_state)

    @classmethod
    def from_json(cls, json_data):
        """
        Create a person from json data

        :param dict json_data: The person as a dict in json format
        :return: A new person if pubkey wasn't known, else a new person instance.
        """
        pubkey = json_data['pubkey']
        uid = json_data['uid']
        local_state = LocalState[json_data['local_state']]
        blockchain_state = BlockchainState[json_data['blockchain_state']]

        return cls(uid, pubkey, local_state, blockchain_state)

    @asyncio.coroutine
    def selfcert(self, community):
        """
        Get the identity self certification.
        This request is not cached in the person object.

        :param cutecoin.core.community.Community community: The community target to request the self certification
        :return: A SelfCertification ucoinpy object
        :rtype: ucoinpy.documents.certification.SelfCertification
        """
        timestamp = 0
        lookup_data = yield from community.bma_access.future_request(qtbma.wot.Lookup, req_args={'search': self.pubkey})
        for result in lookup_data['results']:
            if result["pubkey"] == self.pubkey:
                uids = result['uids']
                for uid_data in uids:
                    if uid_data["meta"]["timestamp"] > timestamp:
                        timestamp = uid_data["meta"]["timestamp"]
                        uid = uid_data["uid"]
                        signature = uid_data["self"]

                return SelfCertification(PROTOCOL_VERSION,
                                         community.currency,
                                         self.pubkey,
                                         timestamp,
                                         uid,
                                         signature)
        return None

    def get_join_date(self, community):
        """
        Get the person join date.
        This request is not cached in the person object.

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: A datetime object
        """
        search = community.bma_access.get(self, qtbma.blockchain.Membership, {'search': self.pubkey})
        if search != qtbma.blockchain.Membership.null_value:
            if len(search['memberships']) > 0:
                membership_data = search['memberships'][0]
                block = community.bma_access.get(self, qtbma.blockchain.Block,
                                req_args={'number': membership_data['blockNumber']})
                if block != qtbma.blockchain.Block.null_value:
                    return block['medianTime']
            return None
        else:
            raise MembershipNotFoundError(self.pubkey, community.name)

    def get_expiration_date(self, community):
        try:
            join_block_number = self.membership(community)['blockNumber']
            try:
                join_block = community.bma_access.get(self, qtbma.blockchain.Block,
                                req_args={'number': join_block_number})

                parameters = community.bma_access.get(self, qtbma.blockchain.Parameters)
                if join_block != qtbma.blockchain.Block.null_value \
                        and parameters != qtbma.blockchain.Parameters.null_value:
                    join_date = join_block['medianTime']
                    expiration_date = join_date + parameters['sigValidity']
                else:
                    return None
            except NoPeerAvailable:
                expiration_date = None
        except MembershipNotFoundError:
            expiration_date = None
        return expiration_date


#TODO: Manage 'OUT' memberships ? Maybe ?
    def membership(self, community):
        """
        Get the person last membership document.

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: The membership data in BMA json format
        """
        search = community.bma_access.get(self, qtbma.blockchain.Membership,
                                           {'search': self.pubkey})
        if search != qtbma.blockchain.Membership.null_value:
            block_number = -1
            for ms in search['memberships']:
                if ms['blockNumber'] > block_number:
                    block_number = ms['blockNumber']
                    if 'type' in ms:
                        if ms['type'] is 'IN':
                            membership_data = ms
                    else:
                        membership_data = ms
            return membership_data
        else:
            raise MembershipNotFoundError(self.pubkey, community.name)

    def published_uid(self, community):
        data = community.bma_access.get(self, qtbma.wot.Lookup,
                                 req_args={'search': self.pubkey})
        if data != qtbma.wot.Lookup.null_value:
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
        return False

    def is_member(self, community):
        """
        Check if the person is a member of a community

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: True if the person is a member of a community
        """
        certifiers = community.bma_access.get(self, qtbma.wot.CertifiersOf, {'search': self.pubkey})
        if certifiers != qtbma.wot.CertifiersOf.null_value:
            return certifiers['isMember']
        return False

    def certifiers_of(self, identities_registry, community):
        """
        Get the list of this person certifiers

        :param cutecoin.core.registry.identities.IdentitiesRegistry identities_registry: The identities registry
        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: The list of the certifiers of this community
        """
        data = community.bma_access.get(self, qtbma.wot.CertifiersOf, {'search': self.pubkey})

        certifiers = list()

        if data == qtbma.wot.CertifiersOf.null_value:
            logging.debug('bma.wot.CertifiersOf request error')
            data = community.bma_access.get(self, qtbma.wot.Lookup, {'search': self.pubkey})
            if data == qtbma.wot.Lookup.null_value:
                logging.debug('bma.wot.Lookup request error')
            else:
                for result in data['results']:
                    if result["pubkey"] == self.pubkey:
                        for uid_data in result['uids']:
                            for certifier_data in uid_data['others']:
                                for uid in certifier_data['uids']:
                                    # add a certifier
                                    certifier = {}
                                    certifier['identity'] = identities_registry.from_handled_data(uid, certifier_data['pubkey'],
                                                                          BlockchainState.BUFFERED)
                                    block = community.bma_access.get(self, qtbma.blockchain.Block,
                                                                         {'number': certifier_data['meta']['block_number']})
                                    certifier['cert_time'] = block['medianTime']
                                    certifiers.append(certifier)
        else:
            for certifier_data in data['certifications']:
                certifier = {}
                certifier['identity'] = identities_registry.from_handled_data(certifier_data['uid'],
                                                                              certifier_data['pubkey'],
                                                                              BlockchainState.VALIDATED)
                certifier['cert_time'] = certifier_data['cert_time']['medianTime']
                certifiers.append(certifier)
        return certifiers

    def unique_valid_certifiers_of(self, identities_registry, community):
        certifier_list = self.certifiers_of(identities_registry, community)
        unique_valid = []
        #  add certifiers of uid
        for certifier in tuple(certifier_list):
            # add only valid certification...
            if community.certification_expired(certifier['cert_time']):
                continue

            # keep only the latest certification
            already_found = [c['identity'].pubkey for c in unique_valid]
            if certifier['identity'].pubkey in already_found:
                index = already_found.index(certifier['identity'].pubkey)
                if certifier['cert_time'] > unique_valid[index]['cert_time']:
                    unique_valid[index] = certifier
            else:
                unique_valid.append(certifier)
        return unique_valid

    def certified_by(self, identities_registry, community):
        """
        Get the list of persons certified by this person

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: The list of the certified persons of this community in BMA json format
        """
        data = community.bma_access.get(self, qtbma.wot.CertifiedBy, {'search': self.pubkey})
        certified_list = list()
        if data == qtbma.wot.CertifiedBy.null_value:
            logging.debug('bma.wot.CertifiersOf request error')
            data = community.bma_access.get(self, qtbma.wot.Lookup, {'search': self.pubkey})
            if data == qtbma.wot.Lookup.null_value:
                logging.debug('bma.wot.Lookup request error')
            else:
                for result in data['results']:
                    if result["pubkey"] == self.pubkey:
                        for certified_data in result['signed']:
                            certified = {}
                            certified['identity'] = identities_registry.from_handled_data(certified_data['uid'],
                                                                              certified_data['pubkey'],
                                                                              BlockchainState.BUFFERED)
                            certified['cert_time'] = certified_data['meta']['timestamp']
                            certified_list.append(certified)
        else:
            for certified_data in data['certifications']:
                certified = {}
                certified['identity'] = identities_registry.from_handled_data(certified_data['uid'],
                                                                              certified_data['pubkey'],
                                                                              BlockchainState.VALIDATED)
                certified['cert_time'] = certified_data['cert_time']['medianTime']
                certified_list.append(certified)
        return certified_list

    def unique_valid_certified_by(self, identities_registry, community):
        certified_list = self.certified_by(identities_registry, community)
        unique_valid = []
        #  add certifiers of uid
        for certified in tuple(certified_list):
            # add only valid certification...
            if community.certification_expired(certified['cert_time']):
                continue

            # keep only the latest certification
            already_found = [c['identity'].pubkey for c in unique_valid]
            if certified['identity'].pubkey in already_found:
                index = already_found.index(certified['identity'].pubkey)
                if certified['cert_time'] > unique_valid[index]['cert_time']:
                    unique_valid[index] = certified
            else:
                unique_valid.append(certified)
        return unique_valid

    def membership_expiration_time(self, community):
        join_block = self.membership(community)['blockNumber']
        join_date = community.get_block(join_block)['medianTime']
        parameters = community.parameters
        expiration_date = join_date + parameters['sigValidity']
        current_time = time.time()
        return expiration_date - current_time

    def jsonify(self):
        """
        Get the community as dict in json format.
        :return: The community as a dict in json format
        """
        data = {'uid': self.uid,
                'pubkey': self.pubkey,
                'local_state': self.local_state.name,
                'blockchain_state': self.blockchain_state.name}
        return data

    def __str__(self):
        return "{0} - {1} - {2} - {3}".format(self.uid,
                                        self.pubkey,
                                        self.local_state,
                                        self.blockchain_state)
