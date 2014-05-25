'''
Created on 1 févr. 2014

@author: inso
'''

import ucoin
import hashlib
import json
import logging
import time
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

    def send_pubkey(self, account, wallets):
        ascii_key = account.gpg.export_keys(account.keyid)
        ascii_key = ascii_key.replace("\n", "\r\n")
        signature = account.gpg.sign(ascii_key, keyid=account.keyid, detach=True)
        print(ascii_key)
        print(signature)
        try:
            wallets.post(ucoin.pks.Add(),
                         {'keytext': ascii_key,
                          'keysign': signature})
        except ValueError as e:
            return str(e)

    def send_membership(self, account, wallets, membership):
        context_data = {'version': 1,
                        'currency': self.currency,
                        'fingerprint': account.fingerprint(),
                        'date': int(time.time()),
                        'membership': membership
                        }
        message = """Version: %(version)d
Currency: %(currency)s
Registry: MEMBERSHIP
Issuer: %(fingerprint)s
Date: %(date)s
Membership: %(membership)s
""" % context_data

        message = message.replace("\n", "\r\n")
        signature = account.gpg.sign(message, keyid=account.keyid, detach=True)
        try:
            wallets.post(ucoin.registry.community.Members(),
                    {'membership': message, 'signature': signature})
        except ValueError as e:
            return str(e)

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
