'''
Created on 11 févr. 2014

@author: inso
'''
from cutecoin.models.community import Community
from cutecoin.models.node import MainNode
import ucoinpy as ucoin

def createCommunity(mainNode):
    community = Community()
    community.knownNodes.append(mainNode)
    currentAmendment = community.ucoinRequest(ucoin.hdc.amendments.Current())
    community.currency = currentAmendment['currency']
    return community


def loadCommunity(jsonData):
    community = Community()
    for nodeData in jsonData['nodes']:
        community.knownNodes.append(MainNode(nodeData['server'], nodeData['port']))
    community.currency = jsonData['currency']
    return community

