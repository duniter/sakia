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

from .. import HDC

class Base(HDC):
    def __init__(self):
        super().__init__('hdc/transactions')

class Process(Base):
    """POST a transaction."""

    def __init__(self, transaction, signature):
        """
        Arguments:
        - `transaction`: The raw transaction.
        - `signature`: The signature of the transaction.
        """

        super().__init__()

        self.transaction = transaction
        self.signature = signature

    def post(self):
        pass

class All(Base):
    """GET all the transactions stored by this node."""

    def get(self):
        """creates a generator with one transaction per iteration."""

        return self.merkle_easy_parser('/all')

class Keys(Base):
    """GET PGP keys for which some transactions have been recoreded by this node (sent and received)."""

    def get(self):
        """creates a generator with one key per iteration."""

        return self.merkle_easy_parser('/keys')

class Last(Base):
    """GET the last received transaction."""

    def __init__(self, count=None):
        """
        Arguments:
        - `count`: Integer indicating to retrieve the last [COUNT] transactions.
        """

        super().__init__()

        self.count = count

    def get(self):
        if not self.count:
            return self.requests_get('/last').json()

        return self.requests_get('/last/%d' % self.count).json()

class Sender(Base):
    """GET all the transactions sent by this sender and stored by this node (should contain all transactions of the sender)."""

    def __init__(self, pgp_fingerprint):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        """

        super().__init__()

        self.pgp_fingerprint = pgp_fingerprint

    def get(self):
        return self.merkle_easy_parser('/sender/%s' % self.pgp_fingerprint)

class Recipient(Base):
    """GET all the transactions received for this recipient stored by this node."""

    def __init__(self, pgp_fingerprint):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        """

        super().__init__()

        self.pgp_fingerprint = pgp_fingerprint

    def get(self):
        return self.merkle_easy_parser('/recipient/%s' % self.pgp_fingerprint)

class View(Base):
    """GET the transaction of given TRANSACTION_ID."""

    def __init__(self, transaction_id):
        """
        Arguments:
        - `transaction_id`: The transaction unique identifier.
        """

        super().__init__()

        self.transaction_id = transaction_id

    def get(self):
        return self.requests_get('/view/%s' % self.transaction_id).json()

from . import sender
