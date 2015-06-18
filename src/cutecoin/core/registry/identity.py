'''
Created on 11 févr. 2014

@author: inso
'''

import logging
import time

from ucoinpy.documents.certification import SelfCertification
from cutecoin.tools.exceptions import Error, LookupFailureError,\
                                        MembershipNotFoundError
from cutecoin.core.net.api import bma as qtbma
from cutecoin.core.net.api.bma import PROTOCOL_VERSION
from PyQt5.QtCore import QObject, pyqtSignal


class Identity(QObject):
    """
    A person with a uid and a pubkey
    """
    FOUND = 1
    NOT_FOUND = 0

    inner_data_changed = pyqtSignal(int)

    def __init__(self, uid, pubkey, status):
        """
        Initializing a person object.

        :param str uid: The person uid, also known as its uid on the network
        :param str pubkey: The person pubkey
        :param int status: The local status of the identity
        """
        super().__init__()
        assert(status in (Identity.FOUND, Identity.NOT_FOUND))
        self.uid = uid
        self.pubkey = pubkey
        self.status = status

    @classmethod
    def empty(cls, pubkey):
        return cls("", pubkey, Identity.NOT_FOUND)

    @classmethod
    def from_metadata(cls, metadata):
        return cls(metadata["text"], metadata["id"], Identity.NOT_FOUND)

    @classmethod
    def from_json(cls, json_data):
        """
        Create a person from json data

        :param dict json_data: The person as a dict in json format
        :return: A new person if pubkey wasn't known, else a new person instance.
        """
        pubkey = json_data['pubkey']
        uid = json_data['uid']
        status = json_data['status']

        return cls(uid, pubkey, status)

    def selfcert(self, community):
        """
        Get the person self certification.
        This request is not cached in the person object.

        :param cutecoin.core.community.Community community: The community target to request the self certification
        :return: A SelfCertification ucoinpy object
        :rtype: ucoinpy.documents.certification.SelfCertification
        """
        data = community.bma_access.get(self, qtbma.wot.Lookup, req_args={'search': self.pubkey})
        if data != qtbma.wot.Lookup.null_value:
            timestamp = 0

            for result in data['results']:
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
                return community.get_block(membership_data['blockNumber']).mediantime
            else:
                return None
        else:
            raise MembershipNotFoundError(self.pubkey, community.name)

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
        '''
        Check if the person is a member of a community

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: True if the person is a member of a community
        '''
        certifiers = community.bma_access.get(self, qtbma.wot.CertifiersOf, {'search': self.pubkey})
        if certifiers != qtbma.wot.CertifiersOf.null_value:
            return certifiers['isMember']
        return False

    def certifiers_of(self, community):
        """
        Get the list of this person certifiers

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: The list of the certifiers of this community in BMA json format
        """
        certifiers = community.bma_access.get(self, qtbma.wot.CertifiersOf, {'search': self.pubkey})
        if certifiers == qtbma.wot.CertifiersOf.null_value:
            logging.debug('bma.wot.CertifiersOf request error')
            data = community.bma_access.get(self, qtbma.wot.Lookup, {'search': self.pubkey})
            if data == qtbma.wot.Lookup.null_value:
                logging.debug('bma.wot.Lookup request error')
                return list()

            # convert api data to certifiers list
            certifiers = list()
            # add certifiers of uid

            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    for uid_data in result['uids']:
                        for certifier_data in uid_data['others']:
                            for uid in certifier_data['uids']:
                            # add a certifier
                                certifier = {}
                                certifier['uid'] = uid
                                certifier['pubkey'] = certifier_data['pubkey']
                                certifier['isMember'] = certifier_data['isMember']
                                certifier['cert_time'] = dict()
                                certifier['cert_time']['medianTime'] = community.get_block(
                                    certifier_data['meta']['block_number']).mediantime
                                certifiers.append(certifier)

            return certifiers
        return certifiers['certifications']

    def unique_valid_certifiers_of(self, community):
        certifier_list = self.certifiers_of(community)
        unique_valid = []
        #  add certifiers of uid
        for certifier in tuple(certifier_list):
            # add only valid certification...
            if community.certification_expired(certifier['cert_time']['medianTime']):
                continue

            # keep only the latest certification
            already_found = [c['pubkey'] for c in unique_valid]
            if certifier['pubkey'] in already_found:
                index = already_found.index(certifier['pubkey'])
                if certifier['cert_time']['medianTime'] > unique_valid[index]['cert_time']['medianTime']:
                    unique_valid[index] = certifier
            else:
                unique_valid.append(certifier)
        return unique_valid

    def certified_by(self, community):
        '''
        Get the list of persons certified by this person

        :param cutecoin.core.community.Community community: The community target to request the join date
        :return: The list of the certified persons of this community in BMA json format
        '''
        certified_list = community.bma_access.get(self, qtbma.wot.CertifiedBy, {'search': self.pubkey})
        if certified_list == qtbma.wot.CertifiedBy.null_value:
            logging.debug('bma.wot.CertifiersOf request error')
            data = community.bma_access.get(self, qtbma.wot.Lookup, {'search': self.pubkey})
            if data == qtbma.wot.Lookup.null_value:
                logging.debug('bma.wot.Lookup request error')
                return list()
            else:
                certified_list = list()
                for result in data['results']:
                    if result["pubkey"] == self.pubkey:
                        for certified in result['signed']:
                            certified['cert_time'] = dict()
                            certified['cert_time']['medianTime'] = certified['meta']['timestamp']
                            certified_list.append(certified)

            return certified_list

        return certified_list['certifications']

    def unique_valid_certified_by(self, community):
        certified_list = self.certified_by(community)
        unique_valid = []
        #  add certifiers of uid
        for certified in tuple(certified_list):
            # add only valid certification...
            if community.certification_expired(certified['cert_time']['medianTime']):
                continue

            # keep only the latest certification
            already_found = [c['pubkey'] for c in unique_valid]
            if certified['pubkey'] in already_found:
                index = already_found.index(certified['pubkey'])
                if certified['cert_time']['medianTime'] > unique_valid[index]['cert_time']['medianTime']:
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
        '''
        Get the community as dict in json format.
        :return: The community as a dict in json format
        '''
        data = {'uid': self.uid,
                'pubkey': self.pubkey,
                'status': self.status}
        return data
