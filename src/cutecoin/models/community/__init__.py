'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import hashlib
import json

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
        members = self.ucoinRequest(lambda : self.ucoinInstance.hdc.amendments.view.Members().get)
        return members

    def ucoinRequest(self, request):
        for node in self.knownNodes:
            if node.available == True:
                self.ucoinInstance.settings['server'] = node.server
                self.ucoinInstance.settings['port'] = node.port
                print("Trying to connect to : " + node.getText())
                return (request())()

        raise RuntimeError("Cannot connect to any node")


    def currentAmendmentId(self):
        currentAmendment = self.ucoinRequest(lambda:ucoin.hdc.amendments.Current().get)
        currentAmendmentHash = hashlib.sha1(json.dumps(currentAmendment).encode('utf-8')).hexdigest()
        amendmentId = str(currentAmendment["number"]) + "-" + currentAmendmentHash
        print("Amendment : " + amendmentId)
        return amendmentId

    def name(self):
        return self.currency

    #TODO: Jsonify this model
    def saveJson(self):
        pass

