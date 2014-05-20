'''
Created on 5 févr. 2014

@author: inso
'''
from cutecoin.models.community import Community
import ucoin
import logging


class Communities(object):

    '''
    The list of the communities an account is member of.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.communities_list = []

    def add_community(self, wallets):
        '''
        Add a community with a mainNode
        '''
        community = Community.create(wallets)
        if community not in self.communities_list:
            self.communities_list.append(community)
            return community
        return None

    def jsonify(self, wallets):
        '''
        Return the list of communities in a key:value form.
        '''
        data = []
        for community in self.communities_list:
            data.append(community.jsonify(wallets))
        return data
