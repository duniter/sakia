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
            if com.currency == currency:
                return com

    def addCommunity(self, mainNode):
        ucoin.settings['server'] = mainNode.server
        ucoin.settings['port'] = mainNode.port
        currentAmendment = ucoin.hdc.amendments.Promoted().get()
        currency = currentAmendment['currency']
        community = self.getCommunity(currency)
        if community == None:
            community = Community(mainNode, currency)
            self.communitiesList.append(community)

        return community