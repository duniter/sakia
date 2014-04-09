'''
Created on 7 févr. 2014

@author: inso
'''

from cutecoin.models.wallet import Wallet


class Wallets(object):

    '''
    The list of the wallets owned by an account.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.wallets_list = []

    def add_wallet(self, community):
        '''
        Create a new wallet of a specific currency.
        This wallet must not already be present in the account,
        it means the wallet must have a different name or a different currency.
        '''
        wallet = Wallet.create(community)
        if wallet not in self.wallets_list:
            self.wallets_list.append(wallet)
            return wallet
        else:
            return self.wallets_list.get(wallet)

    def get_wallet(self, wallet):
        '''
        Look for a wallet in the wallets list.
        '''
        for w in self.wallets_list:
            if w == wallet:
                return w
        return None

    def remove_all_wallets_of(self, community):
        for wallet in self.wallets_list:
            if wallet.community == community:
                self.wallets_list.remove(wallet)

    def jsonify(self, community):
        '''
        Return the list of wallets in a key:value form.
        '''
        community_wallets = [
            w for w in self.wallets_list if w.community == community]
        data = []
        for wallet in community_wallets:
            data.append(wallet.jsonify())
        return data
