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
    def __init__(self):
        '''
        Constructor
        '''
        self.knownNodes = []
        self.currency = ""

    def membersFingerprints(self):
        '''
        Listing members of a community
        '''
        fingerprints = self.ucoinRequest(ucoin.hdc.amendments.view.Members(self.amendmentId()))
        members = []
        for f in fingerprints:
            members.append(f['value'])
        return members

    def issuances(self):
        '''
        Listing issuances the accounted emitted
        '''
        #TODO:Return issuances
        #issuances = self.ucoinRequest(ucoin.hdc.amendments.view.Members(amendmentId)
        return []

    def ucoinRequest(self, request, get_args={}):
        for node in self.knownNodes:
                logging.debug("Trying to connect to : " + node.getText())
                request.server = node.server
                request.port = node.port
                return request.get(**get_args)

        raise RuntimeError("Cannot connect to any node")


    def amendmentId(self):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        currentAmendmentHash = hashlib.sha1(currentAmendment['raw'].encode('utf-8')).hexdigest().upper()
        amendmentId = str(currentAmendment["number"]) + "-" + currentAmendmentHash
        logging.debug("Amendment : " + amendmentId)
        return amendmentId

    def name(self):
        return self.currency

    def jsonifyNodesList(self):
        data = []
        for node in self.knownNodes:
            data.append(node.jsonify())
        return data

    def jsonify(self):
        data = {'nodes' : self.jsonifyNodesList(),
                'currency' : self.currency}
        return data

