'''
Created on 12 févr. 2014

@author: inso
'''
import ucoinpy as ucoin

from cutecoin.models.person import factory
from cutecoin.models.transaction import Transfer, Issuance

def createTransaction(senderFingerprint, increment, community):
    transactionId = senderFingerprint + "-" + str(increment)
    ucoinTransactionView = ucoin.hdc.transactions.View(transactionId)
    ucoinTransaction = ucoinTransactionView['transaction']
    transaction = None
    if ucoinTransaction['type']  == 'TRANSFER':
        transaction = Transfer()
    elif ucoinTransaction['type']  == 'ISSUANCE':
        transaction = Issuance()

    if transaction != None:
        transaction.increment = increment
        transaction.community = community
        transaction.sender = factory.createPerson(senderFingerprint, community)
        transaction.recipient = factory.createPerson(ucoinTransaction['recipient'], community)

    return transaction
