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

from .. import HDC, logging

logger = logging.getLogger("ucoin/hdc/transactions")

class Base(HDC):
    def __init__(self, server=None, port=None):
        super().__init__('hdc/transactions', server, port)

class Process(Base):
    """POST a transaction."""

    def __post__(self, **kwargs):
        assert 'transaction' in kwargs
        assert 'signature' in kwargs

        return self.requests_post('/process', **kwargs).json()

class All(Base):
    """GET all the transactions stored by this node."""

    def __get__(self, **kwargs):
        """creates a generator with one transaction per iteration."""

        return self.merkle_easy_parser('/all')

class Keys(Base):
    """GET PGP keys for which some transactions have been recoreded by this node (sent and received)."""

    def __get__(self, **kwargs):
        """creates a generator with one key per iteration."""

        return self.merkle_easy_parser('/keys')

class Last(Base):
    """GET the last received transaction."""

    def __init__(self, count=None, server=None, port=None):
        """
        Arguments:
        - `count`: Integer indicating to retrieve the last [COUNT] transactions.
        """

        super().__init__(server, port)

        self.count = count

    def __get__(self, **kwargs):
        if not self.count:
            return self.requests_get('/last', **kwargs).json()

        return self.requests_get('/last/%d' % self.count, **kwargs).json()

class Sender(Base):
    """GET all the transactions sent by this sender and stored by this node (should contain all transactions of the sender)."""

    def __init__(self, pgp_fingerprint, begin=None, end=None, server=None, port=None):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        - `begin`: integer value used by the merkle parser to know when to begin requesting.
        - `end`: integer value used by the merkle parser to know when to end requesting.
        """

        super().__init__(server, port)

        self.pgp_fingerprint = pgp_fingerprint
        self.begin = begin
        self.end = end

    def __get__(self, **kwargs):
        return self.merkle_easy_parser('/sender/%s' % self.pgp_fingerprint, begin=self.begin, end=self.end)

class Recipient(Base):
    """GET all the transactions received for this recipient stored by this node."""

    def __init__(self, pgp_fingerprint, begin=None, end=None, server=None, port=None):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        - `begin`: integer value used by the merkle parser to know when to begin requesting.
        - `end`: integer value used by the merkle parser to know when to end requesting.
        """

        super().__init__(server, port)

        self.pgp_fingerprint = pgp_fingerprint
        self.begin = begin
        self.end = end

    def __get__(self, **kwargs):
        return self.merkle_easy_parser('/recipient/%s' % self.pgp_fingerprint, begin=self.begin, end=self.end)

class View(Base):
    """GET the transaction of given TRANSACTION_ID."""

    def __init__(self, transaction_id, server=None, port=None):
        """
        Arguments:
        - `transaction_id`: The transaction unique identifier.
        """

        super().__init__(server, port)

        self.transaction_id = transaction_id

    def __get__(self, **kwargs):
        return self.requests_get('/view/%s' % self.transaction_id, **kwargs).json()

from . import sender
