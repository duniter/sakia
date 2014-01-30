#!/usr/bin/env python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#

import hashlib, logging
from .. import pks, ucg, hdc, settings

logger = logging.getLogger("wrappers")

class Wrapper:
    def __call__(self):
        pass

class Transaction(Wrapper):
    def __init__(self, type, pgp_fingerprint, message=''):
        self.pgp_fingerprint = pgp_fingerprint
        self.message = message
        self.type = type

    def __call__(self):
        try:
            last_tx = hdc.transactions.sender.Last(self.pgp_fingerprint).get()
        except ValueError:
            last_tx = None

        context_data = {}
        context_data.update(settings)
        context_data['version'] = 1
        context_data['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
        context_data['previousHash'] = hashlib.sha1(("%(raw)s%(signature)s" % last_tx).encode('ascii')).hexdigest().upper() if last_tx else None
        context_data['message'] = self.message
        context_data['type'] = self.type
        context_data.update(self.get_context_data())

        tx = """\
Version: %(version)d
Currency: %(currency)s
Sender: %(fingerprint)s
Number: %(number)d
""" % context_data

        if last_tx: tx += "PreviousHash: %(previousHash)s\n" % context_data

        tx += self.get_message(context_data)

        tx += """\
Comment:
%(message)s
""" % context_data

        tx = tx.replace("\n", "\r\n")
        txs = settings['gpg'].sign(tx, detach=True)

        return self.process(tx, txs)

    def get_context_data(self):
        return {}

    def get_message(self, context_data, tx=''):
        return tx

    def process(self, tx, txs):
        try:
            hdc.transactions.Process().post(transaction=tx, signature=txs)
        except ValueError as e:
            print(e)
        else:
            return True

        return False

class Transfer(Transaction):
    def __init__(self, pgp_fingerprint, recipient, coins, message=''):
        super().__init__('TRANSFER', pgp_fingerprint, message)
        self.recipient = recipient
        self.coins = coins

    def get_message(self, context_data, tx=''):
        context_data['recipient'] = self.recipient

        tx += """\
Recipient: %(recipient)s
Type: %(type)s
Coins:
""" % context_data

        for coin in self.coins.split(','):
            data = coin.split(':')
            issuer = data[0]
            for number in data[1:]:
                context_data.update(hdc.coins.View(issuer, int(number)).get())
                tx += '%(id)s, %(transaction)s\n' % context_data

        return tx

class Issue(Transaction):
    def __init__(self, pgp_fingerprint, amendment, coins, message=''):
        super().__init__('ISSUANCE', pgp_fingerprint, message)
        self.amendment = amendment
        self.coins = coins

    def get_next_coin_number(self, coins):
        number = 0
        for c in coins:
            candidate = int(c['id'].split('-')[1])
            if candidate > number: number = candidate
        return number+1

    def get_message(self, context_data, tx=''):
        context_data['amendment'] = self.amendment

        tx += """\
Recipient: %(fingerprint)s
Type: %(type)s
Coins:
""" % context_data

        try:
            last_issuance = hdc.transactions.sender.issuance.Last(self.pgp_fingerprint).get()
        except ValueError:
            last_issuance = None

        previous_idx = 0 if not last_issuance else self.get_next_coin_number(last_issuance['transaction']['coins'])

        for idx, coin in enumerate(self.coins):
            context_data['idx'] = idx+previous_idx
            context_data['base'], context_data['power'] = [int(x) for x in coin.split(',')]
            tx += '%(fingerprint)s-%(idx)d-%(base)d-%(power)d-A-%(amendment)d\n' % context_data

        return tx

class CoinsWrapper(Wrapper):
    def __init__(self, pgp_fingerprint):
        self.pgp_fingerprint = pgp_fingerprint

class CoinsGet(CoinsWrapper):
    def __init__(self, pgp_fingerprint, values):
        super().__init__(pgp_fingerprint)
        self.values = values

    def __call__(self):
        __list = hdc.coins.List(self.pgp_fingerprint).get()
        coins = {}
        for c in __list['coins']:
            for id in c['ids']:
                n,b,p,t,i = id.split('-')
                amount = int(b) * 10**int(p)
                coins[amount] = {'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount}

        issuers = {}
        for v in self.values:
            if v in coins:
                c = coins[v]
                issuers[c['issuer']] = issuers.get(c['issuer']) or []
                issuers[c['issuer']].append(c)
            else:
                raise ValueError('You do not have enough coins of value (%d)' % v)

        res = ''
        for i, issuer in enumerate(issuers):
            if i > 0: res += ','
            res += issuer
            for c in issuers[issuer]:
                res += ':%(number)d' % c

        return res

class CoinsList(CoinsWrapper):
    def __call__(self):
        __list = hdc.coins.List(self.pgp_fingerprint).get()
        coins = []
        __sum = 0
        for c in __list['coins']:
            for id in c['ids']:
                n,b,p,t,i = id.split('-')
                amount = int(b) * 10**int(p)
                __dict = {'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount}
                coins.append(__dict)
                __sum += amount
        return __sum, coins
