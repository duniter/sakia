'''
Created on 11 févr. 2014

@author: inso
'''

import logging
from ucoinpy.api import bma
from ucoinpy import PROTOCOL_VERSION
from ucoinpy.documents.certification import SelfCertification
from cutecoin.tools.exceptions import PersonNotFoundError


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
    def lookup(cls, pubkey, community):
        '''
        Create a person from the pubkey found in a community
        '''
        data = community.request(bma.wot.Lookup, req_args={'search': pubkey})
        results = data['results']
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

    def jsonify(self):
        data = {'name': self.name,
                'pubkey': self.pubkey}
        return data
