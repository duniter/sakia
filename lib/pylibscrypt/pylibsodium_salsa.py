#!/usr/bin/env python

# Copyright (c) 2014 Richard Moore
# Copyright (c) 2014 Jan Varho
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Scrypt implementation that calls into system libsodium"""


import base64
import ctypes, ctypes.util
from ctypes import c_char_p, c_size_t, c_uint64, c_uint32, c_void_p
import hashlib, hmac
import numbers
import struct
import sys

from . import mcf as mcf_mod
from .common import *


def _get_libsodium():
    '''
    Locate the nacl c libs to use
    '''

    __SONAMES = (13, 10, 5, 4)
    # Import libsodium from system
    sys_sodium = ctypes.util.find_library('sodium')
    if sys_sodium is None:
        sys_sodium = ctypes.util.find_library('libsodium')

    if sys_sodium:
        return ctypes.CDLL(sys_sodium)

    # Import from local path
    if sys.platform.startswith('win'):
        try:
            return ctypes.cdll.LoadLibrary('libsodium')
        except OSError:
            pass
        for soname_ver in __SONAMES:
            try:
                return ctypes.cdll.LoadLibrary(
                    'libsodium-{0}'.format(soname_ver)
                )
            except OSError:
                pass
    elif sys.platform.startswith('darwin'):
        try:
            return ctypes.cdll.LoadLibrary('libsodium.dylib')
        except OSError:
            pass
    else:
        try:
            return ctypes.cdll.LoadLibrary('libsodium.so')
        except OSError:
            pass

        for soname_ver in __SONAMES:
            try:
                return ctypes.cdll.LoadLibrary(
                    'libsodium.so.{0}'.format(soname_ver)
                )
            except OSError:
                pass


_libsodium = _get_libsodium()
if _libsodium is None:
    raise ImportError('Unable to load libsodium')

try:
    _libsodium_salsa20_8 = _libsodium.crypto_core_salsa208
except AttributeError:
    raise ImportError('Incompatible libsodium: ')

_libsodium_salsa20_8.argtypes = [
    c_void_p,  # out (16*4 bytes)
    c_void_p,  # in  (4*4 bytes)
    c_void_p,  # k   (8*4 bytes)
    c_void_p,  # c   (4*4 bytes)
]


# Python 3.4+ have PBKDF2 in hashlib, so use it...
if 'pbkdf2_hmac' in dir(hashlib):
    _pbkdf2 = hashlib.pbkdf2_hmac
else:
    # but fall back to Python implementation in < 3.4
    from pbkdf2 import pbkdf2_hmac as _pbkdf2


def scrypt(password, salt, N=SCRYPT_N, r=SCRYPT_r, p=SCRYPT_p, olen=64):
    """Returns a key derived using the scrypt key-derivarion function

    N must be a power of two larger than 1 but no larger than 2 ** 63 (insane)
    r and p must be positive numbers such that r * p < 2 ** 30

    The default values are:
    N -- 2**14 (~16k)
    r -- 8
    p -- 1

    Memory usage is proportional to N*r. Defaults require about 16 MiB.
    Time taken is proportional to N*p. Defaults take <100ms of a recent x86.

    The last one differs from libscrypt defaults, but matches the 'interactive'
    work factor from the original paper. For long term storage where runtime of
    key derivation is not a problem, you could use 16 as in libscrypt or better
    yet increase N if memory is plentiful.
    """
    def array_overwrite(source, s_start, dest, d_start, length):
        dest[d_start:d_start + length] = source[s_start:s_start + length]


    def blockxor(source, s_start, dest, d_start, length):
        for i in xrange(length):
            dest[d_start + i] ^= source[s_start + i]


    def integerify(B, r):
        """A bijection from ({0, 1} ** k) to {0, ..., (2 ** k) - 1"""

        Bi = (2 * r - 1) * 8
        return B[Bi] & 0xffffffff


    def salsa20_8(B, x):
        """Salsa 20/8 using libsodium

        NaCL/libsodium includes crypto_core_salsa208, but unfortunately it
        expects the data in a different order, so we need to mix it up a bit.
        """
        hi = 0xffffffff00000000
        lo = 0x00000000ffffffff
        struct.pack_into('<9Q', x, 0,
            (B[0] & lo) +  (B[2] & hi),  (B[5] & lo) + (B[7] & hi), # c
            B[3], B[4],                                             # in
            B[0], B[1], (B[2] & lo) + (B[5] & hi),                  # pad k pad
            B[6], B[7],
        )

        c = ctypes.addressof(x)
        i = c + 4*4
        k = c + 9*4

        _libsodium_salsa20_8(c, i, k, c)

        B[:] = struct.unpack('<8Q8x', x)


    def blockmix_salsa8(BY, Yi, r):
        """Blockmix; Used by SMix"""

        start = (2 * r - 1) * 8
        X = BY[start:start+8]                              # BlockMix - 1
        x = ctypes.create_string_buffer(8*9)

        for i in xrange(2 * r):                            # BlockMix - 2
            blockxor(BY, i * 8, X, 0, 8)                   # BlockMix - 3(inner)
            salsa20_8(X, x)                                # BlockMix - 3(outer)
            array_overwrite(X, 0, BY, Yi + (i * 8), 8)     # BlockMix - 4

        for i in xrange(r):                                # BlockMix - 6
            array_overwrite(BY, Yi + (i * 2) * 8, BY, i * 8, 8)
            array_overwrite(BY, Yi + (i*2 + 1) * 8, BY, (i + r) * 8, 8)


    def smix(B, Bi, r, N, V, X):
        """SMix; a specific case of ROMix based on Salsa20/8"""

        array_overwrite(B, Bi, X, 0, 16 * r)               # ROMix - 1

        for i in xrange(N):                                # ROMix - 2
            array_overwrite(X, 0, V, i * (16 * r), 16 * r) # ROMix - 3
            blockmix_salsa8(X, 16 * r, r)                  # ROMix - 4

        for i in xrange(N):                                # ROMix - 6
            j = integerify(X, r) & (N - 1)                 # ROMix - 7
            blockxor(V, j * (16 * r), X, 0, 16 * r)        # ROMix - 8(inner)
            blockmix_salsa8(X, 16 * r, r)                  # ROMix - 9(outer)

        array_overwrite(X, 0, B, Bi, 16 * r)               # ROMix - 10

    check_args(password, salt, N, r, p, olen)

    # Everything is lists of 64-bit uints for all but pbkdf2
    try:
        B  = _pbkdf2('sha256', password, salt, 1, p * 128 * r)
        B  = list(struct.unpack('<%dQ' % (len(B) // 8), B))
        XY = [0] * (32 * r)
        V  = [0] * (16 * r * N)
    except (MemoryError, OverflowError):
        raise ValueError("scrypt parameters don't fit in memory")

    for i in xrange(p):
        smix(B, i * 16 * r, r, N, V, XY)

    B = struct.pack('<%dQ' % len(B), *B)
    return _pbkdf2('sha256', password, B, 1, olen)


def scrypt_mcf(password, salt=None, N=SCRYPT_N, r=SCRYPT_r, p=SCRYPT_p,
               prefix=b'$s1$'):
    """Derives a Modular Crypt Format hash using the scrypt KDF

    Parameter space is smaller than for scrypt():
    N must be a power of two larger than 1 but no larger than 2 ** 31
    r and p must be positive numbers between 1 and 255
    Salt must be a byte string 1-16 bytes long.

    If no salt is given, a random salt of 128+ bits is used. (Recommended.)
    """
    return mcf_mod.scrypt_mcf(scrypt, password, salt, N, r, p, prefix)


def scrypt_mcf_check(mcf, password):
    """Returns True if the password matches the given MCF hash"""
    return mcf_mod.scrypt_mcf_check(scrypt, mcf, password)


if __name__ == "__main__":
    import sys
    from . import tests
    tests.run_scrypt_suite(sys.modules[__name__])

