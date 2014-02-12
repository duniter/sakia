'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
from cutecoin.models.coin import Coin
from cutecoin.models.person import factory

class Transaction(object):
    '''
    A transaction which can be a transfer or an issuance.
    At the moment the difference is not made
    '''
    def __init__(self):
        self.increment = 0
        self.community = ""
        self.sender = None
        self.recipient = None

    def value(self):
        value = 0
        trxData = self.community.ucoinRequest(ucoin.hdc.transactions.View(self.sender.pgpFingerprint + "-" + self.increment))
        for coin in trxData['transaction']['coins']:
            value += Coin(coin[id]).value()
        return value

    def currency(self):
        trxData = self.community.ucoinRequest(ucoin.hdc.transactions.View(self.sender.pgpFingerprint + "-" + self.increment))
        currency = trxData['transaction']['currency']
        return currency

    def transactionID(self):
        return self.senderFingerprint + "-" + self.increment



class Transfer(Transaction):
    '''
    A received transaction
    '''
    def __init__(self):
        super(Transfer).__init__()

    def getReceivedText(self):
        return str(self.value) + " " + self.currency + " from " + self.sender.name

    def getSentText(self):
        return str(self.value) + " " + self.currency + " from " + self.recipient.name


class Issuance(Transaction):
    '''
    An issuance
    '''
    def __init__(self):
        super(Issuance).__init__()

    def getText(self):
        return str(self.value) + " " + self.currency




