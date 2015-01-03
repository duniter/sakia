#!/usr/bin/env python

# Copyright (c) 2014, Jan Varho
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""PBKDF2 in pure Python, compatible with Python3.4 hashlib.pbkdf2_hmac"""


import hashlib
import hmac
import struct

from .common import *


def pbkdf2_hmac(name, password, salt, rounds, dklen=None):
    """Returns the result of the Password-Based Key Derivation Function 2"""
    h = hmac.new(key=password, digestmod=lambda d=b'': hashlib.new(name, d))
    hs = h.copy()
    hs.update(salt)

    blocks = bytearray()
    dklen = hs.digest_size if dklen is None else dklen
    block_count, last_size = divmod(dklen, hs.digest_size)
    block_count += last_size > 0

    for block_number in xrange(1, block_count + 1):
        hb = hs.copy()
        hb.update(struct.pack('>L', block_number))
        U = bytearray(hb.digest())

        if rounds > 1:
            Ui = U
            for i in xrange(rounds - 1):
                hi = h.copy()
                hi.update(Ui)
                Ui = bytearray(hi.digest())
                for j in xrange(hs.digest_size):
                    U[j] ^= Ui[j]

        blocks.extend(U)

    if last_size:
        del blocks[dklen:]
    return bytes(blocks)

if __name__ == "__main__":
    import sys
    from . import tests
    tests.run_pbkdf2_suite(sys.modules[__name__])

