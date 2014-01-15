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

import requests, logging, gnupg, json

settings = {
    'host': 'localhost',
    'port': 8081,
    'auth': False,
}

logger = logging.getLogger("ucoin")

class Response:
    """Wrapper of requests.Response class in order to verify signed message."""

    def __init__(self, response):
        """
        Arguments:
        - `self`:
        - `response`:
        """

        self.response = response

        if settings.get('user'):
            logger.debug('selected keyid: %s' % settings.get('user'))
            self.gpg = gnupg.GPG(options=['-u %s' % settings['user']])
        else:
            self.gpg = gnupg.GPG()

        self.status_code = response.status_code
        self.headers = response.headers

        if settings.get('auth'):
            self.verified, clear, self.signature = self.split_n_verify(response)

            if not self.verified:
                raise ValueError('bad signature verification')

            self.text = self.clear_text = clear
            self.content = self.clear_content = self.text.encode('ascii')
        else:
            self.text = response.text
            self.content = response.content

    def json(self):
        if not settings.get('auth'):
            return self.response.json()

        return json.loads(self.text)

    def split_n_verify(self, response):
        """
        Split the signed message thanks to the boundary value got in content-type header.

        returns a tuple with the status, the clear message and the signature.

        `response`: the response returns by requests.get() needed to access to headers and response content.
        """

        begin = '-----BEGIN PGP SIGNATURE-----'
        end = '-----END PGP SIGNATURE-----'
        boundary_pattern = 'boundary='

        content_type = response.headers['content-type']
        boundary = content_type[content_type.index(boundary_pattern)+len(boundary_pattern):]
        boundary = boundary[:boundary.index(';')].strip()

        data = [x.strip() for x in response.text.split('--%s' % boundary)]

        clear = data[1]
        signed = data[2][data[2].index(begin):]
        clearsigned = '-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA1\n\n%s\n%s' % (clear, signed)

        return (bool(self.gpg.verify(clearsigned)), clear, signed)

class API:
    """APIRequest is a class used as an interface. The intermediate derivated classes are the modules and the leaf classes are the API requests."""

    def __init__(self, module):
        """
        Asks a module in order to create the url used then by derivated classes.

        Arguments:
        - `module`: module name
        """

        self.url = 'http://%s:%d/%s' % (settings['host'], settings['port'], module)
        self.headers = {}

        if settings['auth']:
            self.headers['Accept'] = 'multipart/signed'

        if settings.get('user'):
            logger.debug('selected keyid: %s' % settings.get('user'))
            self.gpg = gnupg.GPG(options=['-u %s' % settings['user']])
        else:
            self.gpg = gnupg.GPG()

    def reverse_url(self, path):
        """
        Reverses the url using self.url and path given in parameter.

        Arguments:
        - `path`: the request path
        """

        return self.url + path

    def get(self, **kwargs):
        """wrapper of overloaded __get__ method."""

        return self.__get__(**kwargs)

    def post(self, **kwargs):
        """wrapper of overloaded __post__ method."""

        logger.debug('do some work with')

        data = self.__post__(**kwargs)

        logger.debug('and send back')

        return data

    def __get__(self, **kwargs):
        """interface purpose for GET request"""

        pass

    def __post__(self, **kwargs):
        """interface purpose for POST request"""

        pass

    def requests_get(self, path, **kwargs):
        """
        Requests GET wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """

        if not settings.get('auth'):
            return requests.get(self.reverse_url(path), params=kwargs, headers=self.headers)

        return Response(requests.get(self.reverse_url(path), params=kwargs, headers=self.headers))

    def requests_post(self, path, **kwargs):
        """
        Requests POST wrapper in order to use API parameters.

        Arguments:
        - `path`: the request path
        """

        return requests.post(self.reverse_url(path), data=kwargs, headers=self.headers)

    def merkle_easy_parser(self, path):
        root = self.requests_get(path, leaves='true').json()
        for leaf in root['leaves']:
            yield self.requests_get(path, leaf=leaf).json()['leaf']

from . import pks, ucg, hdc
