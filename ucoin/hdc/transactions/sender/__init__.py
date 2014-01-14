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
    """Get the last received transaction of a PGP key."""

    def __init__(self, pgp_fingerprint):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        """

        super().__init__('hdc/transactions/sender/%s' % pgp_fingerprint)

class Last(Base):
    """Get the last received transaction of a PGP key."""

    def __init__(self, pgp_fingerprint, count=None):
        """
        Arguments:
        - `count`: Integer indicating to retrieve the last [COUNT] transactions.
        """

        super().__init__(pgp_fingerprint)

        self.count = count

    def get(self):
        if not self.count:
            return self.requests_get('/last').json()

        return self.requests_get('/last/%d' % self.count).json()

class Transfer(Base):
    """GET all transfer transactions sent by this sender and stored by this node (should contain all transfert transactions of the sender)."""

    def get(self):
        return self.merkle_easy_parser('/transfert')

class Issuance(Base):
    """GET all issuance transactions (forged coins) sent by this sender and stored by this node (should contain all issuance transactions of the sender)."""

    def get(self):
        return self.merkle_easy_parser('/issuance')

from . import issuance
