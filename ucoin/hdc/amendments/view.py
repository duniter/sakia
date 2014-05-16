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

logger = logging.getLogger("ucoin/hdc/amendments/view")


class View(HDC):
    def __init__(self, amendment_id, server=None, port=None):
        super().__init__('hdc/amendments/view/%s' % amendment_id, server, port)


class Self(View):
    """Shows the raw data of the amendment [AMENDMENT_ID]."""

    def __get__(self, **kwargs):
        return self.requests_get('/self', **kwargs).json()


class Signatures(View):
    """GET the signatures of the Community listed in this amendment."""

    def __get__(self, **kwargs):
        return self.merkle_easy_parser('/signatures')
