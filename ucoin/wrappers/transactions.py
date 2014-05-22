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

import hashlib, logging, re
from . import Wrapper, pks, network, hdc, registry, settings

logger = logging.getLogger("transactions")


class Transaction(Wrapper):
    def __init__(self, pgp_fingerprint, recipient, coins, message='', keyid=None, peering=None, server=None, port=None):
        super().__init__(server, port)
        self.keyid = keyid
        self.pgp_fingerprint = pgp_fingerprint
        self.message = message
        self.error = None
        self.peering = peering
        self.recipient = recipient
        self.coins = coins
        self.coins.sort()

    def __call__(self):
        tx = self.get_message()
        txs = settings['gpg'].sign(tx, keyid=self.keyid, detach=True)
        return (tx, txs)

    def get_context_data(self):
        return {}

    def get_message(self):
        try:
            last_tx = hdc.transactions.sender.Last(count=1, pgp_fingerprint=self.pgp_fingerprint,
                                                   server=self.server, port=self.port).get()
            last_tx = last_tx['transactions'][0]
            last_tx = hdc.transactions.sender.View(self.pgp_fingerprint, tx_number=last_tx['number'],
                                                   server=self.server, port=self.port).get()
        except ValueError:
            last_tx = None

        if last_tx:
            previous_hash = hashlib.sha1(("%s%s" % (last_tx['raw'], last_tx['transaction']['signature'])).encode('ascii')).hexdigest().upper()
        else:
            previous_hash = None

        context_data = {}
        context_data.update(settings)
        context_data.update(self.peering if self.peering else network.Peering(server=self.server, port=self.port).get())
        context_data['version'] = 1
        context_data['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
        context_data['previousHash'] = previous_hash
        context_data['message'] = self.message
        context_data['fingerprint'] = self.pgp_fingerprint
        context_data['recipient'] = self.recipient
        context_data.update(self.get_context_data())

        tx = """\
Version: %(version)d
Currency: %(currency)s
Sender: %(fingerprint)s
Number: %(number)d
""" % context_data

        if last_tx: tx += "PreviousHash: %(previousHash)s\n" % context_data


        tx += """\
Recipient: %(recipient)s
Coins:
""" % context_data

        for coin in self.coins:
            tx += '%s' % coin
            ownership = hdc.coins.view.Owner(coin, self.server, self.port).get()
            if 'transaction' in ownership:
                tx += ':%(transaction)s\n' % ownership
            else:
                tx += "\n"

        return tx

        tx += """\
Comment:
%(message)s""" % context_data

        tx = tx.replace("\n", "\r\n")
        return tx

    def get_error(self):
        return self.error

