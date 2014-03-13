'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
import hashlib
import json
import logging

from cutecoin.models.node import Node
from cutecoin.models.wallet import Wallet

class Community(object):
    '''
    classdocs
    '''
    def __init__(self, nodes):
        '''
        A community is a group of nodes using the same currency.
        They are all using the same amendment and are syncing their datas.
        An account is a member of a community if he is a member of the current amendment.
        '''
        self.nodes = nodes
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        self.currency = currentAmendment['currency']

    @classmethod
    def create(cls, mainNode):
        nodes = []
        nodes.append(mainNode)
        return cls(nodes)


    @classmethod
    def load(cls, jsonData, account):
        knownNodes = []
        for nodeData in jsonData['nodes']:
            knownNodes.append(Node(nodeData['server'], nodeData['port'], nodeData['trust'], nodeData['hoster']))

        community = cls(knownNodes)

        for walletsData in jsonData['wallets']:
            wallet = Wallet.load(walletsData, community)
            wallet.refreshCoins(account.keyFingerprint())
            account.wallets.walletsList.append(wallet)
        return community


    #TODO: Check if its working
    def _searchTrustAddresses(self, trustFg, nextNode, traversedNodes):
        nextFg = nextNode.peering()['fingerprint']
        if nextFg not in traversedNodes:
            traversedNodes.append(nextFg)
            if trustFg == nextFg:
                return trustFg
            else:
                for peer in nextNode.peers():
                    # Look for next node informations
                    found = self._searchTrustAddresses(trustFg, Node(peer['ipv4'], int(peer['port'])), traversedNodes)
                    if found is not None:
                        return found
        return None

    def synchronizeTrusts(self, trustsFingerprints):
        trusts = []
        for trustFg in trustsFingerprints:
            trusts.append(self._searchTrustAddresses(trustFg, self.trusts()[0]))
        return trusts

    def trusts(self):
        return [node for node in self.nodes if node.trust]

    def hosters(self):
        return [node for node in self.nodes if node.trust]

    def membersFingerprints(self):
        '''
        Listing members of a community
        '''
        fingerprints = self.ucoinRequest(ucoin.hdc.amendments.view.Members(self.amendmentId()))
        members = []
        for f in fingerprints:
            members.append(f['value'])
        return members

    def ucoinRequest(self, request, get_args={}):
        for node in self.trusts():
                logging.debug("Trying to connect to : " + node.getText())
                request = node.use(request)
                return request.get(**get_args)
        raise RuntimeError("Cannot connect to any node")


    def ucoinPost(self, request, get_args={}):
        for node in self.hosters():
                logging.debug("Trying to connect to : " + node.getText())
                request = node.use(request)
                return request.post(**get_args)
        raise RuntimeError("Cannot connect to any node")

    def amendmentId(self):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        currentAmendmentHash = hashlib.sha1(currentAmendment['raw'].encode('utf-8')).hexdigest().upper()
        amendmentId = str(currentAmendment["number"]) + "-" + currentAmendmentHash
        logging.debug("Amendment : " + amendmentId)
        return amendmentId

    def __eq__(self, other):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        currentAmendmentHash = hashlib.sha1(currentAmendment['raw'].encode('utf-8')).hexdigest().upper()

        otherAmendment = other.ucoinRequest(ucoin.hdc.amendments.Current())
        otherAmendmentHash = hashlib.sha1(otherAmendment['raw'].encode('utf-8')).hexdigest().upper()

        return (otherAmendmentHash == currentAmendmentHash)

    def name(self):
        return self.currency

    def dividend(self):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        return currentAmendment['dividend']

    def coinMinimalPower(self):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        if 'coinMinimalPower' in currentAmendment.keys():
            return currentAmendment['coinMinimalPower']
        else:
            return 0

    def amendmentNumber(self):
        currentAmendment = self.ucoinRequest(ucoin.hdc.amendments.Current())
        return currentAmendment['number']

    def jsonifyNodesList(self):
        data = []
        for node in self.nodes:
            data.append(node.jsonify())
        return data

    def jsonify(self, wallets):
        data = {'nodes' : self.jsonifyNodesList(),
                'currency' : self.currency,
                'wallets' : wallets.jsonify(self)}
        return data

