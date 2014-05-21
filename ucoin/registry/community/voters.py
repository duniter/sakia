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
#

from . import Base
from .. import logging

logger = logging.getLogger("ucoin/registry/community")

class Current(Base):
    """GET the last valid membership document for member pgp_fingerprint"""

    def __init__(self, pgp_fingerprint=None, server=None, port=None):
        """
        Uses number to fit the result.

        Arguments:
        - `number`: amendment number
        """

        super().__init__(server=server, port=port)

        self.pgp_fingerprint = pgp_fingerprint

    def __get__(self, **kwargs):
        return self.requests_get('/voters/%s/current' % self.pgp_fingerprint,
                                 **kwargs).json()


class History(Base):
    """GET the all received and stored membership documents"""

    def __init__(self, pgp_fingerprint=None, server=None, port=None):
        """
        Uses number to fit the result.

        Arguments:
        - `number`: amendment number
        """

        super().__init__(server=server, port=port)

        self.pgp_fingerprint = pgp_fingerprint

    def __get__(self, **kwargs):
        return self.requests_get('/voters/%s/history' % self.pgp_fingerprint,
                                 **kwargs).json()
