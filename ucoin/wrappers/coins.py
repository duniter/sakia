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

import logging
from . import Wrapper, pks, network, hdc, settings

logger = logging.getLogger("coins")

class Coins(Wrapper):
    def __init__(self, pgp_fingerprint, server=None, port=None):
        super().__init__(server, port)

        self.pgp_fingerprint = pgp_fingerprint

class Get(Coins):
    def __init__(self, pgp_fingerprint, values, server=None, port=None):
        super().__init__(pgp_fingerprint, server, port)

        self.values = values

    def __call__(self):
        __list = hdc.coins.List(self.pgp_fingerprint, self.server, self.port).get()
        coins = {}
        for c in __list['coins']:
            for id in c['ids']:
                n,b,p,t,i = id.split('-')
                amount = int(b) * 10**int(p)
                if amount not in coins: coins[amount] = []
                coins[amount].append({'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount})

        issuers = {}
        for v in self.values:
            if v in coins and coins[v]:
                c = coins[v].pop()
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

class List(Coins):
    def __init__(self, pgp_fingerprint, limit=None, server=None, port=None):
        super().__init__(pgp_fingerprint, server, port)

        self.limit = limit

    def __call__(self):
        __list = hdc.coins.List(self.pgp_fingerprint, self.server, self.port).get()
        coins = []
        __sum = 0

        for c in __list['coins']:
            for id in c['ids']:
                n,b,p,t,i = id.split('-')
                amount = int(b) * 10**int(p)
                __dict = {'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount}

                if not self.limit or self.limit >= amount:
                    coins.append(__dict)
                    __sum += amount

        return __sum, coins
