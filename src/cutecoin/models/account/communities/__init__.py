'''
Created on 5 févr. 2014

@author: inso
'''
from cutecoin.models.community import Community
import logging


class Communities(object):

    '''
    The list of the communities an account is member of.
    '''

    def __init__(self, _communities_list):
        '''
        Constructor
        '''
        self._communities_list = _communities_list

    @classmethod
    def create(cls):
        return cls([])

    @classmethod
    def load(cls, json_data):
        _communities_list = []
        for community_data in json_data:
            _communities_list.append(Community.load(community_data))
        return cls(_communities_list)

    def __iter__(self):
        return self._communities_list.__iter__()

    def __contains__(self, wallet):
        return wallet in self._communities_list

    def __reverse__(self):
        return self._communities_list.__reverse__()

    def __len__(self):
        return len(self._communities_list)

    def __getitem__(self, key):
        return self._communities_list[key]

    def add_community(self, wallets):
        '''
        Add a community with a mainNode
        '''
        community = Community.create(wallets)
        if community not in self._communities_list:
            self._communities_list.append(community)
            return community
        return None

    def request(self, request, get_args={}):
        response = None
        for community in self._communities_list:
            try:
                response = community.request(request, get_args)
            except:
                continue
            return response

    def post(self, request, get_args={}):
        for community in self._communities_list:
            try:
                response = community.post(request, get_args)
            except:
                continue
            return response

    def jsonify(self):
        '''
        Return the list of communities in a key:value form.
        '''
        data = []
        for community in self._communities_list:
            data.append(community.jsonify())
        return data
