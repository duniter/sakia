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

from .. import API, logging

logger = logging.getLogger("ucoin/network")

class Network(API):
    def __init__(self, module='network', server=None, port=None):
        super().__init__(module, server, port)

class Pubkey(Network):
    """GET the public key of the peer."""

    def __get__(self, **kwargs):
        return self.requests_get('/pubkey', **kwargs).text

class Peering(Network):
    """GET peering information about a peer."""

    def __get__(self, **kwargs):
        return self.requests_get('/peering', **kwargs).json()

class THT(Network):
    """GET/POST THT entries."""

    def __init__(self, pgp_fingerprint=None, server=None, port=None):
        """
        Use the pgp fingerprint parameter in order to fit the result.

        Arguments:
        - `pgp_fingerprint`: pgp fingerprint to use as a filter
        """

        super().__init__(server, port)

        self.pgp_fingerprint = pgp_fingerprint

    def __get__(self, **kwargs):
        if not self.pgp_fingerprint:
            return self.merkle_easy_parser('/tht')

        return self.merkle_easy_parser('/tht/%s' % self.pgp_fingerprint).json()

    def __post__(self, **kwargs):
        assert 'entry' in kwargs
        assert 'signature' in kwargs

        return self.requests_post('/tht', **kwargs)

from . import peering
