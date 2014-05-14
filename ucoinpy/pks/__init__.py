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

from .. import API
from .. import logging

logger = logging.getLogger("ucoin/pks")


class PKS(API):
    def __init__(self, module='pks', server=None, port=None):
        super().__init__(module, server, port)


class Add(PKS):
    """POST ASCII-armored OpenPGP certificates."""

    def __post__(self, **kwargs):
        assert 'keytext' in kwargs
        assert 'keysign' in kwargs

        return self.requests_post('/add', **kwargs)


class Lookup(PKS):
    """Allows to search for OpenPGP certificates, according to HKP draft."""

    def __get__(self, **kwargs):
        assert 'search' in kwargs
        assert 'op' in kwargs

        r = self.requests_get('/lookup', **kwargs)

        if kwargs['op'] == 'get': return r.text

        return r.json()


class All(PKS):
    """GET all the received public keys."""

    def __get__(self, **kwargs):
        """creates a generator with one public key per iteration."""

        return self.merkle_easy_parser('/all')
