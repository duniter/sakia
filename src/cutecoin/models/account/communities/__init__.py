'''
Created on 5 févr. 2014

@author: inso
'''
import ucoinpy as ucoin
from cutecoin.models.community import Community
from cutecoin.core.exceptions import NotMemberOfCommunityError
import logging

class Communities(object):
    '''
    The list of the communities an account is member of.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.communitiesList = []

    def addCommunity(self, mainNode, keyFingerprint):
        '''
        Add a community with a mainNode and the pgpFingerprint of the account
        Check if the pgpFingerprint is present in the community members list
        If its not, the account isnt added and an error is raised.
        '''
        community = Community.create(mainNode)
        members = community.ucoinRequest(ucoin.hdc.amendments.view.Members(community.amendmentId()))

        logging.debug("Account fingerprint : " + keyFingerprint)
        for member in members:
            logging.debug(member)
            if member['value'] == keyFingerprint:
                self.communitiesList.append(community)
                return community

        raise NotMemberOfCommunityError(keyFingerprint, community.currency + "-" + community.amendmentId())


    def jsonify(self, wallets):
        '''
        Return the list of communities in a key:value form.
        '''
        data = []
        for community in self.communitiesList:
            data.append(community.jsonify(wallets))
        return data



