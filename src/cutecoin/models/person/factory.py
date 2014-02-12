'''
Created on 11 févr. 2014

@author: inso
'''
from cutecoin.core.exceptions import PersonNotFoundError
from cutecoin.models.person import Person
import ucoinpy as ucoin


def createPerson(pgpFingerprint, community):
        '''
        Create a person from the pgpFingerprint found in a community
        '''
        keys = community.ucoinRequest(ucoin.pks.Lookup(),
                                          get_args={'search':"0x"+pgpFingerprint, 'op':'index'})['keys']
        if len(keys) > 0:
            person = Person()
            json = keys[0]['key']
            person.name = json['name']
            person.fingerprint = json['fingerprint']
            person.email = json['email']
            return person
        else:
            raise PersonNotFoundError(pgpFingerprint, "pgpFingerprint", community)
        return None

def createPersonFromJson(jsonPerson):
    '''
    Create a person from json data
    '''
    person = Person()
    person.name = jsonPerson['name']
    person.pgpFingerprint = jsonPerson['fingerprint']
    person.email = jsonPerson['email']
    pass