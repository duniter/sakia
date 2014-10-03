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

logger = logging.getLogger("ucoin/blockchain")

class Blockchain(API):
    def __init__(self, connection_handler, module='blockchain'):
        super(Blockchain, self).__init__(connection_handler, module)

class Parameters(Blockchain):
    """GET the blockchain parameters used by this node."""

    def __get__(self, **kwargs):
        return self.requests_get('/parameters', **kwargs).json()

class Membership(Blockchain):
    """POST a Membership document."""

    def __post__(self, **kwargs):
        assert 'membership' in kwargs

        return self.requests_post('/membership', **kwargs).json()

class Block(Blockchain):
    """GET/POST a block from/to the blockchain."""

    def __init__(self, connection_handler, number=None):
        """
        Use the number parameter in order to select a block number.

        Arguments:
        - `number`: block number to select
        """

        super(Block, self).__init__(connection_handler)

        self.number = number

    def __get__(self, **kwargs):
        assert self.number is not None
        return self.requests_get('/block/%d' % self.number, **kwargs).json()

    def __post__(self, **kwargs):
        assert 'block' in kwargs
        assert 'signature' in kwargs

        return self.requests_post('/block', **kwargs).json()

class Current(Blockchain):
    """GET, same as block/[number], but return last accepted block."""

    def __get__(self, **kwargs):
        return self.requests_get('/current', **kwargs).json()

class Hardship(Blockchain):
    """GET hardship level for given member's fingerprint for writing next block."""

    def __init__(self, connection_handler, fingerprint):
        """
        Use the number parameter in order to select a block number.

        Arguments:
        - `fingerprint`: member fingerprint
        """

        super(Hardship, self).__init__(connection_handler)

        self.fingerprint = fingerprint

    def __get__(self, **kwargs):
        assert self.fingerprint is not None
        return self.requests_get('/hardship/%s' % self.fingerprint.upper(), **kwargs).json()
