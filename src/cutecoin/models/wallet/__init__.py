'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import logging
import gnupg
import json
from cutecoin.models.coin import Coin
from cutecoin.tools.exceptions import CommunityNotFoundError


class Wallet(object):

    '''
    A wallet is list of coins.
    It's only used to sort coins.
    '''

    def __init__(self, fingerprint, coins, community, name):
        '''
        Constructor
        '''
        self.coins = coins
        self.fingerprint = fingerprint
        self.community = community
        self.name = name

    @classmethod
    def create(cls, fingerprint, community, name):
        return cls(fingerprint, [], community, name)

    @classmethod
    def load(cls, json_data, community):
        coins = []
        for coinData in json_data['coins']:
            coins.append(Coin.from_id(coinData['coin']))
        return cls(coins, community)

    def __eq__(self, other):
        return (self.community == other.community)

    def value(self):
        value = 0
        for coin in self.coins:
            value += coin.value()
        return value

    # TODO: Refresh coins when changing current account
    def refresh_coins(self):
        data_list = self.community.network.request(
            ucoin.hdc.coins.List({'pgp_fingerprint': self.fingerprint}))
        for issuances in data_list['coins']:
            issuer = issuances['issuer']
            for coins_ids in issuances['ids']:
                shortened_id = coins_ids
                coin = Coin.from_id(issuer + "-" + shortened_id)
                self.coins.append(coin)


    #TODO: Adapt to new WHT
    def tht(self, community):
        if community in self.communities.communities_list:
            #tht = community.ucoinRequest(ucoin.wallets.tht(self.fingerprint()))
            #return tht['entries']
            return None
        return None

    def push_tht(self, community):
        if community in self.communities.communities_list:
            hosters_fg = []
            trusts_fg = []
            for trust in community.network.trusts():
                peering = trust.peering()
                logging.debug(peering)
                trusts_fg.append(peering['fingerprint'])
            for hoster in community.network.hosters():
                logging.debug(peering)
                peering = hoster.peering()
                hosters_fg.append(peering['fingerprint'])
            entry = {
                'version': '1',
                'currency': community.currency,
                'fingerprint': self.fingerprint(),
                'hosters': hosters_fg,
                'trusts': trusts_fg
            }
            logging.debug(entry)
            json_entry = json.JSONEncoder(indent=2).encode(entry)
            gpg = gnupg.GPG()
            signature = gpg.sign(json_entry, keyid=self.keyid, clearsign=True)

            dataPost = {
                'entry': entry,
                'signature': str(signature)
            }

            #community.network.post(
            #    ucoin.ucg.THT(
            #        pgp_fingerprint=self.fingerprint()),
            #    dataPost)
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def pull_tht(self, community):
        if community in self.communities.communities_list:
            community.pull_tht(self.fingerprint())
        else:
            raise CommunityNotFoundError(self.keyid, community.amendment_id())

    def get_text(self):
        return self.name + " : " + \
            str(self.value()) + " " + self.community.currency

    def jsonify_coins_list(self):
        data = []
        for coin in self.coins:
            data.append({'coin': coin.get_id()})
        return data

    def jsonify(self):
        return {'coins': self.jsonify_coins_list(),
                'name': self.name}
