'''
Created on 7 févr. 2014

@author: inso
'''

from cutecoin.models.wallet import factory

class Wallets(object):
    '''
    The list of the wallets owned by an account.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.walletsList = []

    def addWallet(self, currency):
        '''
        Create a new wallet of a specific currency.
        This wallet must not already be present in the account,
        it means the wallet must have a different name or a different currency.
        '''
        wallet = factory.createWallet(currency)
        if wallet not in self.walletsList:
            self.walletsList.append(wallet)
        else:
            return self.walletsList.get(wallet)

    def getWallet(self, wallet):
        '''
        Look for a wallet in the wallets list.
        '''
        for w in self.walletsLists:
            if w == wallet:
                return w
        return None

    def jsonify(self, community):
        '''
        Return the list of wallets in a key:value form.
        '''
        communityWallets = [w for w in self.walletsList if w.community == community]
        data = []
        for wallet in communityWallets:
            data.append(wallet.jsonify())
        return data

