'''
Created on 5 févr. 2014

@author: inso
'''
import ucoinpy as ucoin
from cutecoin.models.community import Community

class Communities(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.communitiesList = []

    def getCommunity(self, currency):
        for com in self.communitiesList:
            #TODO: Compare communities by amendment hash instead of currency
            if com.currency == currency:
                return com

    def addCommunity(self, mainNode, accountFingerprint):
        community = Community(mainNode)
        self.members = community.ucoinRequest(lambda:ucoin.hdc.amendments.view.Members(community.currentAmendmentId()).get)

        print(accountFingerprint)
        for member in self.members:
            print(member)
            if member['value'] == accountFingerprint:
                self.communitiesList.append(community)
                return community

        return None

    #TODO: Jsonify this model
    def saveJson(self):
        pass
