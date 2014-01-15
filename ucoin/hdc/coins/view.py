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

logger = logging.getLogger("ucoin/hdc/coins/view")

class Base(HDC):
    def __init__(self, pgp_fingerprint, coin_number):
        super().__init__('hdc/coins/%s/view/%d' % (pgp_fingerprint, coin_number))

class History(Base):
    """GET a transaction history of the coin [COIN_NUMBER] issued by [PGP_FINGERPRINT]."""

    def __get__(self, **kwargs):
        return self.requests_get('/history').json()
