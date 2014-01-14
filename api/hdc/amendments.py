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

from . import HDC

class Base(HDC):
    def __init__(self):
        super().__init__('hdc/amendments')

class List(Base):
    """GET the list of amendments through the previousHash value."""

    def get(self):
        """creates a generator with one amendment per iteration."""

        current = self.requests_get('/current').json()
        yield current

        while 'previousHash' in current and current['previousHash']:
            current['previousNumber'] = current['number']-1
            current = self.requests_get('/view/%(previousNumber)d-%(previousHash)s/self' % current).json()
            yield current
