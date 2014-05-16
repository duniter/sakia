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

from .. import Registry
from .. import logging

logger = logging.getLogger("ucoin/registry")


class Base(Registry):
    def __init__(self, server=None, port=None):
        super().__init__('registry/amendment', server, port)


class Vote(Base):

    """GET the vote of current node for given amendment number
    (both amendment + signature).
    Such vote may be used by any node to broadcast the whole network."""

    def __init__(self, am_number=None, server=None, port=None):
        super().__init__(server, port)

    def __get__(self, **kwargs):
        return self.merkle_easy_parser('/%s/vote' % self.am_number)
