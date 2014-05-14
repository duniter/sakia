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

from ... import HDC
from ... import logging

logger = logging.getLogger("ucoin/hdc/transactions/sender")


class Base(HDC):
    """Get the last received transaction of a PGP key."""

    def __init__(self, pgp_fingerprint, server=None, port=None):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key
         we want to see sent transactions.
        """

        super().__init__('hdc/transactions/sender/%s' % pgp_fingerprint,
                          server, port)


class Last(Base):
    """Get the last received transaction of a PGP key."""

    def __init__(self, pgp_fingerprint, count=None, from_=None,
                server=None, port=None):
        """
        Arguments:
        - `count`: Integer indicating to retrieve the last [COUNT] transactions
        """

        super().__init__(pgp_fingerprint, server, port)

        self.count = count
        self.from_ = from_

    def __get__(self, **kwargs):
        if not self.count:
            return self.requests_get('/last', **kwargs).json()

        if not self.from_:
            return self.request_get('/last/%d' % self.count, **kwargs).json()

        return self.requests_get('/last/%d/%d' % (self.count, self.from_),
                                  **kwargs).json()


class View(Base):
    """GET the transaction of given TRANSACTION_ID."""

    def __init__(self, pgp_fingerprint, tx_number,
                  server=None, port=None):
        """
        Arguments:
        - `count`: Integer indicating to retrieve the last [COUNT] transactions
        """

        super().__init__(pgp_fingerprint, server, port)

        self.tx_number = tx_number

    def __get__(self, **kwargs):
        return self.requests_get('/view/%d' % self.tx_number, **kwargs).json()
