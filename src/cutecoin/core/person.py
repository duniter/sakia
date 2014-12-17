'''
Created on 11 févr. 2014

@author: inso
'''

import logging
from ucoinpy.api import bma
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
        logging.debug(data)
        results = data['results']
        if len(results) > 0:
            uids = results[0]['uids']
            if len(uids) > 0:
                name = uids[0]["uid"]
            else:
                raise PersonNotFoundError(pubkey, community.name())
                return None
        else:
            raise PersonNotFoundError(pubkey, community.name())
            return None
        return cls(name, pubkey)

    @classmethod
    def from_json(cls, json_person):
        '''
        Create a person from json data
        '''
        name = json_person['name']
        pubkey = json_person['pubkey']
        return cls(name, pubkey)

    def jsonify(self):
        data = {'name': self.name,
                'pubkey': self.pubkey}
        return data
