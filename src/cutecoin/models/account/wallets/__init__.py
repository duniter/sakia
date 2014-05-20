'''
Created on 7 févr. 2014

@author: inso
'''

import logging
from cutecoin.models.wallet import Wallet


class Wallets(object):

    '''
    The list of the wallets owned by an account.
    '''

    def __init__(self, wallets_list):
        '''
        Constructor
        '''
        self._wallets_list = wallets_list

    @classmethod
    def create(cls):
        return cls([])

    @classmethod
    def load(cls, json_data):
        wallets_list = []
        for wallet_data in json_data:
            wallets_list.append(Wallet.load(wallet_data))
        return cls(wallets_list)

    def __iter__(self):
        return self._wallets_list.__iter__()

    def __contains__(self, wallet):
        return wallet in self._wallets_list

    def __reverse__(self):
        return self._wallets_list.__reverse__()

    def __len__(self):
        return len(self._wallets_list)

    def __getitem__(self, key):
        return self._wallets_list[key]

    def add_wallet(self, keyid, community, node,
                   required_trusts=1, name="Main Wallet"):
        '''
        Create a new wallet of a specific currency.
        This wallet must not already be present in the account,
        it means the wallet must have a different name or a different currency.
        '''
        wallet = Wallet.create(keyid, community, node,
                               required_trusts, name)
        if wallet not in self._wallets_list:
            self._wallets_list.append(wallet)
            return wallet
        else:
            return self._wallets_list.get(wallet)

    def community_wallets(self, currency):
        return Wallets([w for w in self._wallets_list if w.currency == currency])

    def request(self, request, get_args={}):
        for wallet in self._wallets_list:
            try:
                response = wallet.request(request, get_args)
            except:
                pass
            return response

    def post(self, request, get_args={}):
        for wallet in self._wallets_list:
            try:
                response = wallet.post(request, get_args)
            except:
                pass
            return response

    def jsonify(self):
        '''
        Return the list of wallets in a key:value form.
        '''
        data = []
        for wallet in self._wallets_list:
            data.append(wallet.jsonify())
        return data
