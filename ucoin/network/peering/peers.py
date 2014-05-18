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
from .. import Network
from .. import logging

logger = logging.getLogger("ucoin/network/peering/peers")

class Base(Network):
    def __init__(self, server=None, port=None):
        super().__init__('network/peering/peers', server, port)

class Stream(Base):
    """GET a list of peers this node is listening to/by for ANY incoming transaction."""

    def __init__(self, request, pgp_fingerprint=None, server=None, port=None):
        """
        Use the pgp fingerprint parameter in order to fit the result.

        Arguments:
        - `request`: select the stream request
        - `pgp_fingerprint`: pgp fingerprint to use as a filter
        """

        super().__init__(server, port)

        self.request = request
        self.pgp_fingerprint = pgp_fingerprint

    def __get__(self, **kwargs):
        """returns the corresponding peer list."""
        if self.pgp_fingerprint is None:
            return self.requests_get('/%s' % (self.request), **kwargs).json()
        else:
            return self.requests_get('/%s/%s' % (self.request, self.pgp_fingerprint), **kwargs).json()


class UpStream(Stream):
    """GET a list of peers this node is listening to for ANY incoming transaction."""

    def __init__(self, pgp_fingerprint=None, server=None, port=None):
        """
        Use the pgp fingerprint parameter in order to fit the result.

        Arguments:
        - `pgp_fingerprint`: pgp fingerprint to use as a filter
        """

        super().__init__('upstream', pgp_fingerprint, server, port)


class DownStream(Stream):
    """GET a list of peers this node is listening by for ANY incoming transaction."""

    def __init__(self, pgp_fingerprint=None, server=None, port=None):
        """
        Use the pgp fingerprint parameter in order to fit the result.

        Arguments:
        - `pgp_fingerprint`: pgp fingerprint to use as a filter
        """

        super().__init__('downstream', pgp_fingerprint, server, port)
