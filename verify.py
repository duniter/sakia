#!/bin/env python3

import requests, gnupg
from pprint import pprint

def split_n_verify(response):
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

    gpg = gnupg.GPG()

    return (bool(gpg.verify(clearsigned)), clear, signed)

r = requests.get('http://mycurrency.candan.fr:8081/ucg/peering', headers={'Accept': 'multipart/signed'})

verified, clear, signed = split_n_verify(r)

assert verified == True
