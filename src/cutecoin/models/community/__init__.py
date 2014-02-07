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
        self.knownNodes = []
        self.knownNodes.append(mainNode)
        self.currency = currency

    def members(self):
        '''
        Listing members of a community
        '''

        #TODO: Try connecting with nodes of the list if the first fails
        # Maybe create a method
        ucoin.settings['server'] = self.knowNodes[0].server
        ucoin.settings['port'] = self.knowNodes[0].port

        members = ucoin.hdc.amendments.view.Members().get()
        return members

    def nodes(self):
        return self.knownNodes


