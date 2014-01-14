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

class View(HDC):
    def __init__(self, amendment_id):
        super().__init__('hdc/amendments/view/%s' % amendment_id)

class Members(View):
    """GET the members present in the Community for this amendment."""

    def get(self):
        return self.merkle_easy_parser('/members')

class Self(View):
    """Shows the raw data of the amendment [AMENDMENT_ID]."""

    def get(self):
        return self.requests_get('/self').json()

class Voters(View):
    """GET the voters listed in this amendment."""

    def get(self):
        return self.merkle_easy_parser('/voters')

class Signatures(View):
    """GET the signatures of the Community listed in this amendment.

    This URL should give the same result as hdc/amendments/votes/[PREVIOUS_AMENDEMENT_ID] if all votes present in this URL were taken in count as signatures for this AMENDMENT_ID.
    """

    def get(self):
        return self.merkle_easy_parser('/signatures')
