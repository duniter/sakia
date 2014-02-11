'''
Created on 11 févr. 2014

@author: inso
'''
from cutecoin.models.account import Account
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.account.communities import Communities
from cutecoin.models.wallet import factory as walletFactory
from cutecoin.models.community import factory as communityFactory

def createAccount(pgpKeyId, name, communities):
    '''
    Constructor
    '''
    account = Account()
    account.pgpKeyId = pgpKeyId
    account.name = name
    account.communities = communities
    account.wallets = Wallets()
    for community in account.communities.communitiesList:
        wallet = account.wallets.addWallet(community.currency)
        wallet.refreshCoins(community, account.keyFingerprint())
    return account

def loadAccount(jsonData):
    account = Account()
    account.pgpKeyId = jsonData['pgpKeyId']
    account.name = jsonData['name']
    account.communities = Communities()
    for communityData in jsonData['communities']:
        account.communities.communitiesList.append(communityFactory.loadCommunity(communityData))
    account.wallets = Wallets()
    for walletData in jsonData['wallets']:
        account.wallets.walletsList.append(walletFactory.loadWallet(jsonData))
    return account