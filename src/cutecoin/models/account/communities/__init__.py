'''
Created on 5 févr. 2014

@author: inso
'''
from cutecoin.models.community import Community
from cutecoin.core.exceptions import NotMemberOfCommunityError
import ucoinpy as ucoin
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

    def add_community(self, main_node, key_fingerprint):
        '''
        Add a community with a mainNode and the fingerprint of the account
        Check if the fingerprint is present in the community members list
        If its not, the account isnt added and an error is raised.
        '''
        community = Community.create(main_node)
        members = community.ucoin_request(
            ucoin.hdc.amendments.view.Members(
                community.amendment_id()))

        logging.debug("Account fingerprint : " + key_fingerprint)
        for member in members:
            logging.debug(member)
            if member['value'] == key_fingerprint:
                self.communities_list.append(community)
                return community

        raise NotMemberOfCommunityError(
            key_fingerprint,
            community.currency +
            "-" +
            community.amendment_id())

    def jsonify(self, wallets):
        '''
        Return the list of communities in a key:value form.
        '''
        data = []
        for community in self.communitiesList:
            data.append(community.jsonify(wallets))
        return data
