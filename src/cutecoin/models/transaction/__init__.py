'''
Created on 1 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from cutecoin.models.person import Person


class Transaction(object):

    '''
    A transaction which can be a transfer or an issuance.
    At the moment the difference is not made
    '''

    def __init__(self, sender, tx_number, wallet, recipient):
        self.tx_number = tx_number
        self.wallet = wallet
        self.sender = sender
        self.recipient = recipient

    @classmethod
    def create(cls, pubkey, tx_number, wallet):
        return None

    def value(self):
        value = 0
        return value

    def currency(self):
        return ""

    def get_receiver_text(self):
        return str(self.value()) + " from " + self.sender.name

    def get_sender_text(self):
        return str(self.value()) + " to " + self.recipient.name
