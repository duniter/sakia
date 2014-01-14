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

from . import HDC, logging

logger = logging.getLogger("ucoin/hdc/transactions/sender/issuance")

class Base(HDC):
    """Get the received issuance transaction of a PGP key."""

    def __init__(self, pgp_fingerprint):
        """
        Arguments:
        - `pgp_fingerprint`: PGP fingerprint of the key we want to see sent transactions.
        """

        super().__init__('hdc/transactions/sender/%s/issuance' % pgp_fingerprint)

class Last(Base):
    """GET the last received issuance transaction of a PGP key."""

    def __get__(self):
        return self.requests_get('/last').json()

class Fusion(Base):
    """GET all fusion transactions sent by this sender and stored by this node (should contain all fusion transactions of the sender)."""

    def __get__(self):
        return self.merkle_easy_parser('/fusion')

class Dividend(Base):
    """GET all dividend transactions (issuance of new coins) sent by this sender and stored by this node (should contain all dividend transactions of the sender)."""

    def __init__(self, pgp_fingerprint, am_number=None):
        """
        Arguments:
        - `am_number`: amendment number
        """

        super().__init__(pgp_fingerprint)

        self.am_number = am_number

    def __get__(self):
        if not self.am_number:
            return self.merkle_easy_parser('/dividend')

        return self.merkle_easy_parser('/dividend/%d' % self.am_number)
