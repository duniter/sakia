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

__all__ = ['api']

__author__      = 'Caner Candan'
__version__     = '0.0.1'
__nonsense__    = 'uCoin'

import requests

URL = 'http://mycurrency.candan.fr:8081'
AUTH = False

class API:
    """APIRequest is a class used as an interface. The intermediate derivated classes are the modules and the leaf classes are the API requests."""

    def __init__(self, module, url=URL, auth=AUTH):
        """
        Asks a module in order to create the url used then by derivated classes.

        Arguments:
        - `module`: module name
        - `url`: url defining the host and port of the server
        - `auth`: enables to get multipart/signed messages.
        """

        self.url = '%s/%s' % (url, module)
        self.headers = {}

        if auth: self.headers['Accept'] = 'multipart/signed'

    def reverse_url(self, path):
        """
        Reverses the url using self.url and path given in parameter.

        Arguments:
        - `path`: the request path
        """

        return self.url + path

    def get(self):
        """interface purpose for GET request"""

        pass

    def post(self):
        """interface purpose for POST request"""

        pass

    def requests_get(self, path):
        """
        Requests GET wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """

        return requests.get(self.reverse_url(path), headers=self.headers)

    def requests_post(self, path):
        """
        Requests POST wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """

        return requests.post(self.reverse_url(path), headers=self.headers)

    def merkle_easy_parser(self, path):
        root = self.requests_get(path + '?leaves=true').json()
        for leaf in root['leaves']:
            yield self.requests_get(path + '?leaf=%s' % leaf).json()['leaf']

from . import pks, ucg, hdc
