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

    def __init__(self, _wallets_list=[]):
        '''
        Constructor
        '''
        self._wallets_list = _wallets_list

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

    def add_wallet(self, fingerprint, community, node, name="Main Wallet"):
        '''
        Create a new wallet of a specific currency.
        This wallet must not already be present in the account,
        it means the wallet must have a different name or a different currency.
        '''
        wallet = Wallet.create(fingerprint, community, node, name)
        if wallet not in self._wallets_list:
            self._wallets_list.append(wallet)
            return wallet
        else:
            return self._wallets_list.get(wallet)

    def community_wallets(self, currency):
        return Wallets([w for w in self._wallets_list if w.currency == currency])

    def jsonify(self, community):
        '''
        Return the list of wallets in a key:value form.
        '''
        community_wallets = [
            w for w in self._wallets_list if w.community == community]
        data = []
        for wallet in community_wallets:
            data.append(wallet.jsonify())
        return data

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
