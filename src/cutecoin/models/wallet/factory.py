'''
Created on 11 févr. 2014

@author: inso
'''
from cutecoin.models.wallet import Wallet
from cutecoin.models.coin import Coin

def createWallet(currency):
    wallet = Wallet()
    wallet.currency = currency
    return wallet


def loadWallet(jsonData):
    wallet = Wallet()
    for coinData in jsonData['coins']:
        wallet.coins.append(Coin(coinData['coin']))
    wallet.currency = jsonData['currency']
    return wallet

