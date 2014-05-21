'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import hashlib
import json
import logging
from cutecoin.models.node import Node
from cutecoin.models.account.wallets import Wallets


class Community(object):
    '''
    classdocs
    '''
    def __init__(self, currency):
        '''
        A community is a group of nodes using the same currency.
        They are all using the same amendment and are syncing their datas.
        An account is a member of a community if he is a member of the current amendment.
        '''
        self.currency = currency

    @classmethod
    def create(cls, currency):
        return cls(currency)

    @classmethod
    def load(cls, json_data):
        currency = json_data['currency']
        community = cls(currency)
        return community

    def name(self):
        return self.currency

    def __eq__(self, other):
        #current_amendment = self.network.request(ucoin.hdc.amendments.Promoted())
        #current_amendment_hash = hashlib.sha1(
        #    current_amendment['raw'].encode('utf-8')).hexdigest().upper()

        #other_amendment = other.network.request(ucoin.hdc.amendments.Promoted())
        #other_amendment_hash = hashlib.sha1(
        #    other_amendment['raw'].encode('utf-8')).hexdigest().upper()

        return (other.currency == self.currency)

    def dividend(self, wallets):
        current_amendment = wallets.request(ucoin.hdc.amendments.Promoted())
        return int(current_amendment['dividend'])

    def coin_minimal_power(self, wallets):
        current_amendment = wallets.request(ucoin.hdc.amendments.Promoted())
        if 'coinMinimalPower' in current_amendment.keys():
            return int(current_amendment['coinMinimalPower'])
        else:
            return 0

    def amendment_id(self, wallets):
        current_amendment = wallets.request(ucoin.hdc.amendments.Promoted())
        current_amendment_hash = hashlib.sha1(
            current_amendment['raw'].encode('utf-8')).hexdigest().upper()
        amendment_id = str(
            current_amendment["number"]) + "-" + current_amendment_hash
        logging.debug("Amendment : " + amendment_id)
        return amendment_id

    def amendment_number(self, wallets):
        current_amendment = wallets.request(ucoin.hdc.amendments.Promoted())
        return int(current_amendment['number'])

    def person_quality(self, wallets, fingerprint):
        quality = 'nothing'
        voter_req = ucoin.registry.community.voters.Current(fingerprint)
        data = wallets.request(voter_req)
        if data:
            quality = 'voter'
        else:
            member_req = ucoin.registry.community.members.Current(fingerprint)
            data = wallets.request(member_req)
            if data:
                membership = data['membership']
                if membership['membership'] == 'IN':
                    quality = 'member'
        return quality

    def members_fingerprints(self, wallets):
        '''
        Listing members of a community
        '''
        memberships = wallets.request(
            ucoin.registry.community.Members())
        members = []
        for m in memberships:
            members.append(m['membership']['issuer'])
        return members

    def voters_fingerprints(self, wallets):
        '''
        Listing members of a community
        '''
        votings = wallets.request(
            ucoin.registry.community.Voters())
        voters = []
        for v in votings:
            voters.append(v['voting']['issuer'])
        return voters

    def jsonify(self):
        data = {'currency': self.currency}
        return data
