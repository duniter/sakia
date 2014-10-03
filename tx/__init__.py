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

logger = logging.getLogger("ucoin/tx")

class Tx(API):
    def __init__(self, connection_handler, module='tx'):
        super(Tx, self).__init__(connection_handler, module)

class Process(Tx):
    """POST a transaction."""

    def __post__(self, **kwargs):
        assert 'transaction' in kwargs
        assert 'signature' in kwargs

        return self.requests_post('/process', **kwargs).json()
