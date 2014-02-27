'''
Created on 12 févr. 2014

@author: inso
'''
import ucoinpy as ucoin

from cutecoin.models.person import Person
from cutecoin.models.transaction import Transfer, Issuance

#TODO: Passer par des factory + pythonic
def createTransaction(senderFingerprint, increment, community):
    transactionId = senderFingerprint + "-" + str(increment)
    ucoinTransactionView = community.ucoinRequest(ucoin.hdc.transactions.View(transactionId))
    ucoinTransaction = ucoinTransactionView['transaction']
    transaction = None
    if ucoinTransaction['type']  == 'TRANSFER':
        transaction = Transfer()
    elif ucoinTransaction['type']  == 'ISSUANCE':
        transaction = Issuance()

    if transaction != None:
        transaction.increment = increment
        transaction.community = community
        transaction.sender = Person.lookup(senderFingerprint, community)
        transaction.recipient = Person.lookup(ucoinTransaction['recipient'], community)

    return transaction
