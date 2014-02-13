'''
Created on 11 févr. 2014

@author: inso
'''
from cutecoin.models.wallet import Wallet
from cutecoin.models.coin import Coin

def createWallet(community):
    wallet = Wallet()
    wallet.community = community
    return wallet


def loadWallet(jsonData, community):
    wallet = Wallet()
    for coinData in jsonData['coins']:
        wallet.coins.append(Coin(coinData['coin']))
    wallet.community = community
    return wallet

