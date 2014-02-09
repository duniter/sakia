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
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.communitiesList = []

    def getCommunity(self, amendmentId):
        for com in self.communitiesList:
            if com.currentAmendmentId() == amendmentId:
                return com

    def addCommunity(self, mainNode, keyFingerprint):
        community = Community(mainNode)
        self.members = community.ucoinRequest(lambda:ucoin.hdc.amendments.view.Members(community.currentAmendmentId()).get)

        logging.debug("Account fingerprint : " + keyFingerprint)
        for member in self.members:
            logging.debug(member)
            if member['value'] == keyFingerprint:
                self.communitiesList.append(community)
                return community

        raise NotMemberOfCommunityError(keyFingerprint, community.currency + "-" + community.currentAmendmentId())
        return None

    #TODO: Jsonify this model
    def saveJson(self):
        pass
