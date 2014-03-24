'''
Created on 12 févr. 2014

@author: inso
'''
import ucoinpy as ucoin

from cutecoin.models.person import Person
from cutecoin.models.transaction import Transfer, Issuance

# TODO: Passer par des factory + pythonic


def create_transaction(sender_fingerprint, increment, community):
    transaction_id = sender_fingerprint + "-" + str(increment)
    ucoin_transaction_view = community.ucoin_request(
        ucoin.hdc.transactions.View(transaction_id))
    ucoin_transaction = ucoin_transaction_view['transaction']
    transaction = None
    if ucoin_transaction['type'] == 'TRANSFER':
        transaction = Transfer()
    elif ucoin_transaction['type'] == 'ISSUANCE':
        transaction = Issuance()

    if transaction is not None:
        transaction.increment = increment
        transaction.community = community
        transaction.sender = Person.lookup(sender_fingerprint, community)
        transaction.recipient = Person.lookup(
            ucoin_transaction['recipient'],
            community)

    return transaction
