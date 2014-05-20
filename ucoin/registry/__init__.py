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

from .. import API
from .. import logging

logger = logging.getLogger("ucoin/registry")


class Registry(API):
    def __init__(self, module='registry', server=None, port=None):
        super().__init__(module=module, server, port)


class Parameters(Registry):
    """GET parameters used by this community."""

    def __get__(self, **kwargs):
        return self.requests_get('/parameters', **kwargs).json()


class Amendment(Registry):
    """GET parameters used by this community."""

    def __get__(self, **kwargs):
        return self.requests_get('/amendment', **kwargs).json()

from . import amendment
from . import community