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

from .. import HDC
from .. import logging

logger = logging.getLogger("ucoin/hdc/amendments")


class Base(HDC):
    def __init__(self, server=None, port=None):
        super().__init__('hdc/amendments', server, port)


class Promoted(Base):
    """GET the current promoted amendment (amendment
    which received enough votes to be accepted)."""

    def __init__(self, number=None, server=None, port=None):
        """
        Uses number to fit the result.

        Arguments:
        - `number`: amendment number
        """

        super().__init__(server, port)

        self.number = number

    def __get__(self, **kwargs):
        if not self.number:
            return self.requests_get('/promoted', **kwargs).json()

        return self.requests_get('/promoted/%d' % self.number, **kwargs).json()


class Votes(Base):
    """GET an index of votes received by this node."""

    def __get__(self, **kwargs):
        return self.requests_get('/votes', **kwargs).json()

    def __post__(self, **kwargs):
        assert 'amendment' in kwargs
        assert 'signature' in kwargs
        assert 'peer' in kwargs

        return self.requests_post('/votes', **kwargs).json()

from . import view
