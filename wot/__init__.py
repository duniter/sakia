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

logger = logging.getLogger("ucoin/wot")


class WOT(API):
    def __init__(self, connection_handler, module='wot'):
        super(WOT, self).__init__(connection_handler, module)


class Add(WOT):
    """POST Public key data."""

    def __post__(self, **kwargs):
        assert 'pubkey' in kwargs
        assert 'self' in kwargs
        assert 'other' in kwargs

        return self.requests_post('/add', **kwargs).json()


class Lookup(WOT):
    """GET Public key data."""

    def __init__(self, connection_handler, search, module='wot'):
        super(WOT, self).__init__(connection_handler, module)

        self.search = search

    def __get__(self, **kwargs):
        assert self.search is not None

        return self.requests_get('/lookup/%s' % self.search, **kwargs).json()


class All(WOT):
    """GET all the received public keys."""

    def __get__(self, **kwargs):
        """creates a generator with one public key per iteration."""

        return self.merkle_easy_parser('/all')
