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
        A community is a group of nodes using the same currency.
        They are all using the same amendment and are syncing their datas.
        An account is a member of a community if he is a member of the current amendment.
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

    def issuances(self, accountFingerprint):
        '''
        Listing issuances the accounted emitted
        '''
        #TODO:Return issuances
        #issuances = self.ucoinRequest(ucoin.hdc.transactions.sender.Issuance())
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

