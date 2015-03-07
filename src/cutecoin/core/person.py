'''
Created on 11 févr. 2014

@author: inso
'''

import logging
import datetime
from ucoinpy.api import bma
from ucoinpy import PROTOCOL_VERSION
from ucoinpy.documents.certification import SelfCertification
from ucoinpy.documents.membership import Membership
from cutecoin.tools.exceptions import PersonNotFoundError,\
                                        MembershipNotFoundError


class Person(object):

    '''
    A person with a name, a fingerprint and an email
    Created by the person.factory
    '''

    def __init__(self, name, pubkey):
        '''
        Constructor
        '''
        self.name = name
        self.pubkey = pubkey

    @classmethod
    def lookup(cls, pubkey, community, cached=True):
        '''
        Create a person from the pubkey found in a community
        '''
        data = community.request(bma.wot.Lookup, req_args={'search': pubkey},
                                 cached=cached)
        timestamp = 0

        for result in data['results']:
            if result["pubkey"] == pubkey:
                uids = result['uids']
                for uid in uids:
                    if uid["meta"]["timestamp"] > timestamp:
                        timestamp = uid["meta"]["timestamp"]
                        name = uid["uid"]

                return cls(name, pubkey)
        raise PersonNotFoundError(pubkey, community.name())

    @classmethod
    def from_json(cls, json_person):
        '''
        Create a person from json data
        '''
        name = json_person['name']
        pubkey = json_person['pubkey']
        return cls(name, pubkey)

    def selfcert(self, community):
        data = community.request(bma.wot.Lookup, req_args={'search': self.pubkey})
        logging.debug(data)
        timestamp = 0

        for result in data['results']:
            if result["pubkey"] == self.pubkey:
                uids = result['uids']
                for uid in uids:
                    if uid["meta"]["timestamp"] > timestamp:
                        timestamp = uid["meta"]["timestamp"]
                        name = uid["uid"]
                        signature = uid["self"]

                return SelfCertification(PROTOCOL_VERSION,
                                             community.currency,
                                             self.pubkey,
                                             timestamp,
                                             name,
                                             signature)
        raise PersonNotFoundError(self.pubkey, community.name())

    def get_join_date(self, community):
        try:
            search = community.request(bma.blockchain.Membership, {'search': self.pubkey})
            membership_data = None
            if len(search['memberships']) > 0:
                membership_data = search['memberships'][0]
                return datetime.datetime.fromtimestamp(community.get_block(membership_data['blockNumber']).mediantime).strftime("%d/%m/%Y %I:%M")
            else:
                return None
        except ValueError as e:
            if '400' in str(e):
                raise MembershipNotFoundError(self.pubkey, community.name())

    def membership(self, community):
        try:
            search = community.request(bma.blockchain.Membership,
                                               {'search': self.pubkey})
            block_number = -1
            for ms in search['memberships']:
                if ms['blockNumber'] > block_number:
                    block_number = ms['blockNumber']
                    if 'type' in ms:
                        if ms['type'] is 'IN':
                            membership_data = ms
                    else:
                        membership_data = ms

            if membership_data is None:
                raise MembershipNotFoundError(self.pubkey, community.name())
        except ValueError as e:
            if '400' in str(e):
                raise MembershipNotFoundError(self.pubkey, community.name())

        membership = Membership(PROTOCOL_VERSION, community.currency, self.pubkey,
                                membership_data['blockNumber'],
                                membership_data['blockHash'], 'IN', search['uid'],
                                search['sigDate'], None)
        return membership

    def is_member(self, community):
        try:
            certifiers = community.request(bma.wot.CertifiersOf, {'search': self.pubkey})
            return certifiers['isMember']
        except ValueError:
            return False

    def certifiers_of(self, community):
        try:
            certifiers = community.request(bma.wot.CertifiersOf, {'search': self.pubkey})
        except ValueError as e:
            logging.debug('bma.wot.CertifiersOf request ValueError : ' + str(e))
            try:
                data = community.request(bma.wot.Lookup, {'search': self.pubkey})
            except ValueError as e:
                logging.debug('bma.wot.Lookup request ValueError : ' + str(e))
                return list()

            # convert api data to certifiers list
            certifiers = list()
            # add certifiers of uid
            for certifier in data['results'][0]['uids'][0]['others']:
                # for each uid found for this pubkey...
                for uid in certifier['uids']:
                    # add a certifier
                    certifier['uid'] = uid
                    certifier['cert_time'] = dict()
                    certifier['cert_time']['medianTime'] = community.get_block(certifier['meta']['block_number']).mediantime
                    certifiers.append(certifier)

            return certifiers

        except Exception as e:
            logging.debug('bma.wot.CertifiersOf request error : ' + str(e))
            return list()

        return certifiers['certifications']

    def certified_by(self, community):
        try:
            certified_list = community.request(bma.wot.CertifiedBy, {'search': self.pubkey})
        except ValueError as e:
            logging.debug('bma.wot.CertifiersOf request ValueError : ' + str(e))
            try:
                data = community.request(bma.wot.Lookup, {'search': self.pubkey})
            except ValueError as e:
                logging.debug('bma.wot.Lookup request ValueError : ' + str(e))
                return list()
            certified_list = list()
            for certified in data['results'][0]['signed']:
                certified['cert_time'] = dict()
                certified['cert_time']['medianTime'] = certified['meta']['timestamp']
                certified_list.append(certified)

            return certified_list

        except Exception as e:
            logging.debug('bma.wot.CertifiersOf request error : ' + str(e))
            return list()

        return certified_list['certifications']

    def jsonify(self):
        data = {'name': self.name,
                'pubkey': self.pubkey}
        return data
