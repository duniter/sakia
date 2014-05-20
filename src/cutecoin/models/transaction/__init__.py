'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
from cutecoin.models.coin import Coin
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
    def create(cls, pgp_fingerprint, tx_number, wallet):
        transaction_view = wallet.request(
            ucoin.hdc.transactions.sender.View(pgp_fingerprint, tx_number))
        transaction_data = transaction_view['transaction']

        sender = Person.lookup(pgp_fingerprint, wallet)
        recipient = Person.lookup(
            transaction_data['recipient'],
            wallet)

        return cls(Transaction(sender, tx_number, wallet, recipient))

    def value(self):
        value = 0
        trx_data = self.wallet.request(
            ucoin.hdc.transactions.sender.View(self.sender.fingerprint,
                                               self.tx_number))
        for coin in trx_data['transaction']['coins']:
            value += Coin.from_id(coin['id']).value()
        return value

    def currency(self):
        trx_data = self.wallet.request(
            ucoin.hdc.transactions.sender.View(self.sender.fingerprint,
                                        self.tx_number))
        currency = trx_data['transaction']['currency']
        return currency

    def transaction_id(self):
        return self.sender_fingerprint + "-" + self.increment
