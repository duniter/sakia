'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import hashlib
import json
import logging

class Community(object):
    '''
    classdocs
    '''
    def __init__(self, mainNode):
        '''
        Constructor
        '''
        self.knownNodes = []
        self.knownNodes.append(mainNode)
        self.ucoinInstance = ucoin

        currentAmendment = self.ucoinRequest(lambda : self.ucoinInstance.hdc.amendments.Current().get)
        self.currency = currentAmendment['currency']

    def members(self):
        '''
        Listing members of a community
        '''
        membersList = self.ucoinRequest(lambda : self.ucoinInstance.hdc.amendments.view.Members(self.currentAmendmentId()).get)
        members = []
        for m in membersList:
            members.append(m['value'])
        return members

    def ucoinRequest(self, request):
        for node in self.knownNodes:
            if node.available == True:
                self.ucoinInstance.settings['server'] = node.server
                self.ucoinInstance.settings['port'] = node.port
                logging.debug("Trying to connect to : " + node.getText())
                return (request())()

        raise RuntimeError("Cannot connect to any node")


    def currentAmendmentId(self):
        currentAmendment = self.ucoinRequest(lambda:ucoin.hdc.amendments.Current().get)
        currentAmendmentHash = hashlib.sha1(currentAmendment['raw'].encode('utf-8')).hexdigest().upper()
        amendmentId = str(currentAmendment["number"]) + "-" + currentAmendmentHash
        logging.debug("Amendment : " + amendmentId)
        return amendmentId

    def name(self):
        return self.currency

    #TODO: Jsonify this model
    def saveJson(self):
        pass

