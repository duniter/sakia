'''
Created on 11 févr. 2014

@author: inso
'''

import logging
import functools
import datetime
from ucoinpy.api import bma
from ucoinpy import PROTOCOL_VERSION
from ucoinpy.documents.certification import SelfCertification
from ucoinpy.documents.membership import Membership
from cutecoin.tools.exceptions import PersonNotFoundError,\
                                        MembershipNotFoundError
from PyQt5.QtCore import QMutex


def load_cache(json_data):
    for person_data in json_data['persons']:
        person = Person.from_json(person_data)
        Person._instances[person.pubkey] = person


def jsonify_cache():
    data = []
    for person in Person._instances.values():
        data.append(person.jsonify())
    return {'persons': data}


class cached(object):
    '''
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    Delete it to clear it from the cache
    '''
    def __init__(self, func):
        self.func = func

    def __call__(self, inst, community):
        inst._cache_mutex.lock()
        try:
            inst._cache[community.currency]
        except KeyError:
            inst._cache[community.currency] = {}

        try:
            value = inst._cache[community.currency][self.func.__name__]
        except KeyError:
            value = self.func(inst, community)
            inst._cache[community.currency][self.func.__name__] = value

        inst._cache_mutex.unlock()
        return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__repr__

    def __get__(self, inst, objtype):
        if inst is None:
            return self.func
        return functools.partial(self, inst)


class Person(object):
    '''
    A person with a name, a fingerprint and an email
    '''
    _instances = {}

    def __init__(self, name, pubkey, cache):
        '''
        Constructor
        '''
        self.name = name
        self.pubkey = pubkey
        self._cache = cache
        self._cache_mutex = QMutex()

    @classmethod
    def lookup(cls, pubkey, community, cached=True):
        '''
        Create a person from the pubkey found in a community
        '''
        if pubkey in Person._instances:
            return Person._instances[pubkey]
        else:
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

                        person = cls(name, pubkey, {})
                        Person._instances[pubkey] = person
                        logging.debug("{0}".format(Person._instances.keys()))
                        return person
        raise PersonNotFoundError(pubkey, community.name())

    @classmethod
    def from_metadata(cls, metadata):
        name = metadata['text']
        pubkey = metadata['id']
        if pubkey in Person._instances:
            return Person._instances[pubkey]
        else:
            person = cls(name, pubkey, {})
            Person._instances[pubkey] = person
            return person

    @classmethod
    #TODO: Remove name from person, contats should not use the person class
    def from_json(cls, json_person):
        '''
        Create a person from json data
        '''
        pubkey = json_person['pubkey']
        if pubkey in Person._instances:
            return Person._instances[pubkey]
        else:
            name = json_person['name']
            if 'cache' in json_person:
                cache = json_person['cache']
            else:
                cache = {}

            person = cls(name, pubkey, cache)
            Person._instances[pubkey] = person
            return person

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

    @cached
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

        return membership_data

    @cached
    def is_member(self, community):
        try:
            certifiers = community.request(bma.wot.CertifiersOf, {'search': self.pubkey})
            return certifiers['isMember']
        except ValueError:
            return False

    @cached
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

    @cached
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

    def reload(self, func, community):
        self._cache_mutex.lock()
        if community.currency not in self._cache:
            self._cache[community.currency] = {}

        change = False
        try:
            before = self._cache[community.currency][func.__name__]
        except KeyError:
            change = True

        value = func(self, community)

        if not change:
            if type(value) is dict:
                hash_before = (hash(tuple(frozenset(sorted(before.keys())))),
                             hash(tuple(frozenset(sorted(before.items())))))
                hash_after = (hash(tuple(frozenset(sorted(value.keys())))),
                             hash(tuple(frozenset(sorted(value.items())))))
                change = hash_before != hash_after
            elif type(value) is bool:
                change = before != value

        self._cache[community.currency][func.__name__] = value
        self._cache_mutex.unlock()
        return change

    def jsonify(self):
        data = {'name': self.name,
                'pubkey': self.pubkey,
                'cache': self._cache}
        return data
