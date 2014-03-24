'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
from cutecoin.models.coin import Coin


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
        trx_data = self.community.ucoin_request(
            ucoin.hdc.transactions.View(self.sender.fingerprint + "-" + str(self.increment)))
        for coin in trx_data['transaction']['coins']:
            value += Coin.from_id(coin['id']).value()
        return value

    def currency(self):
        trx_data = self.community.ucoin_request(
            ucoin.hdc.transactions.View(self.sender.fingerprint + "-" + str(self.increment)))
        currency = trx_data['transaction']['currency']
        return currency

    def transactionID(self):
        return self.sender_fingerprint + "-" + self.increment


class Transfer(Transaction):

    '''
    A received transaction
    '''

    def __init__(self):
        super(Transfer).__init__()

    def getText(self):
        return str(self.value()) + " " + self.currency() + \
            " from " + self.sender.name


class Issuance(Transaction):

    '''
    An issuance
    '''

    def __init__(self):
        super(Issuance).__init__()

    def amendmentNumber(self):
        self.community.ucoin_request(
            ucoin.hdc.transactions.View(self.sender.fingerprint + "-" + str(self.increment)))

    def getText(self):
        return str(self.value()) + " " + self.currency()
