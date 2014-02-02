'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Community(object):
    '''
    classdocs
    '''


    def __init__(self, mainNode, currency):
        '''
        Constructor
        '''
        self.knowNodes = []
        self.knowNodes.append(mainNode)

    def members(self):
        '''
        Listing members of a community
        '''

        # TODO : Try connecting with nodes of the list
        # if the first fails
        # Maybe create a method
        ucoin.settings['server'] = self.knowNodes[0].address
        ucoin.settings['port'] = self.knowNodes[0].port
        ucoin.settings['auth'] = self.knowNodes[0].auth

        members = ucoin.hdc.amendments.view.Members( ucoin.hdc.amendments.Current )
        return members

class CommunitiesManager(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.communities = []

    def getCommunity(self, currency):
        for com in self.communities:
            if com.currency == currency:
                return com

    def addCommunity(self, node):
        ucoin.settings['server'] = node.address
        ucoin.settings['port'] = node.port
        ucoin.settings['auth'] = node.auth

        currentAmendment = ucoin.hdc.amendments.Current.get(self)
        currency = currentAmendment['currency']
        self.communities.append(Community(node), currency)
