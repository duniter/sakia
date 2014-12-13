'''
Created on 11 févr. 2014

@author: inso
'''

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
        Create a person from the fngerprint found in a community
        '''
        return None

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
