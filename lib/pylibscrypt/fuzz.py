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

"""Fuzzes scrypt function input, comparing two implementations"""

import itertools
import random
from random import randrange as rr
import unittest


class Skip(Exception):
    pass


class Fuzzer(object):
    """Fuzzes function input"""
    def __init__(self, f, args, g=None, pass_good=None, pass_bad=None):
        self.f = f
        self.g = g
        self.args = args
        self.pass_good = pass_good
        self.pass_bad = pass_bad

    @staticmethod
    def get_random_int():
        return int((1<<rr(66)) * 1.3)

    @staticmethod
    def get_random_bytes(lrange=None, skip=None):
        if lrange is None:
            v = bytearray(rr(2**rr(10)))
        else:
            v = bytearray(rr(*lrange))
        for i in range(len(v)):
            v[i] = rr(256)
            while v[i] == skip:
                v[i] = rr(256)
        return bytes(v)

    def get_good_args(self):
        kwargs = {}
        for a in self.args:
            assert isinstance(a, dict)
            if 'opt' in a and a['opt'] and random.randrange(2):
                continue
            if 'val' in a:
                kwargs[a['name']] = a['val']
            elif 'vals' in a:
                kwargs[a['name']] = random.choice(a['vals'])
            elif 'valf' in a:
                kwargs[a['name']] = a['valf']()
            elif 'type' in a and a['type'] == 'int':
                kwargs[a['name']] = self.get_random_int()
            elif 'type' in a and a['type'] == 'bytes':
                kwargs[a['name']] = self.get_random_bytes()
            else:
                raise ValueError
            if 'none' in a and not random.randrange(10):
                kwargs[a['name']] = None
            if 'skip' in a and a['skip'](kwargs[a['name']]):
                if 'opt' in a and a['opt']:
                    del kwargs[a['name']]
                else:
                    raise Skip
        return kwargs

    def get_bad_args(self, kwargs=None):
        kwargs = kwargs or self.get_good_args()
        a = random.choice(self.args)
        if not 'opt' in a:
            if not random.randrange(10):
                del kwargs[a['name']]
                return kwargs
        if not 'type' in a:
            return self.get_bad_args(kwargs)

        if not random.randrange(10):
            wrongtype = [
                self.get_random_int(), self.get_random_bytes(), None,
                1.1*self.get_random_int(), 1.0*self.get_random_int()
            ]
            if a['type'] == 'int':
                del wrongtype[0]
            elif a['type'] == 'bytes':
                del wrongtype[1]
            v = random.choice(wrongtype)
            try:
                if 'valf' in a:
                    if a['valf'](v):
                        return self.get_bad_args(kwargs)
                if 'skip' in a and a['skip'](v):
                    return self.get_bad_args(kwargs)
            except TypeError:
                pass # Surely bad enough
            kwargs[a['name']] = v
            return kwargs

        if a['type'] == 'int':
            v = self.get_random_int()
            if 'valf' in a:
                if a['valf'](v):
                    return self.get_bad_args(kwargs)
            if 'skip' in a and a['skip'](v):
                return self.get_bad_args(kwargs)
            kwargs[a['name']] = v
            return kwargs

        if a['type'] == 'bytes' and 'valf' in a:
            v = self.get_random_bytes()
            if not a['valf'](v):
                kwargs[a['name']] = v
                return kwargs

        return self.get_bad_args(kwargs)

    def fuzz_good_run(self, tc):
        try:
            kwargs = self.get_good_args()
            r1 = self.f(**kwargs)
            r2 = self.g(**kwargs) if self.g is not None else None
            if self.g is not None:
                r2 = self.g(**kwargs)
        except Skip:
            tc.skipTest('slow')
        except Exception as e:
            assert False, ('unexpected exception', kwargs, e)

        try:
            if self.pass_good:
                tc.assertTrue(self.pass_good(r1, r2, kwargs),
                              msg=('unexpected output', r1, r2, kwargs))
            else:
                if self.g is not None:
                    assert r1 == r2, ('f and g mismatch', kwargs, r1, r2)
                tc.assertTrue(r1)
        except Exception as e:
            print ('unexpected exception', kwargs, r1, r2, e)
            raise

    def fuzz_bad(self, f=None, kwargs=None):
        f = f or self.f
        kwargs = kwargs or self.get_bad_args()
        return f(**kwargs)

    def fuzz_bad_run(self, tc):
        try:
            kwargs = self.get_bad_args()
        except Skip:
            tc.skipTest('slow')
        for f in ((self.f,) if not self.g else (self.f, self.g)):
            try:
                r = self.fuzz_bad(f, kwargs)
                assert False, ('no exception', kwargs, r)
            except Skip:
                tc.skipTest('slow')
            except AssertionError:
                raise
            except Exception:
                pass

    def testcase_good(self, tests=1, name='FuzzTestGood'):
        testfs = {}
        for i in range(tests):
            testfs['test_fuzz_good_%d' % i] = lambda s: self.fuzz_good_run(s)
        t = type(name, (unittest.TestCase,), testfs)
        return t

    def testcase_bad(self, tests=1, name='FuzzTestBad'):
        testfs = {}
        for i in range(tests):
            testfs['test_fuzz_bad_%d' % i] = lambda s: self.fuzz_bad_run(s)
        t = type(name, (unittest.TestCase,), testfs)
        return t

    def generate_tests(self, suite, count, name):
        loader = unittest.defaultTestLoader
        suite.addTest(
            loader.loadTestsFromTestCase(
                self.testcase_good(count, name + 'Good')
            )
        )
        suite.addTest(
            loader.loadTestsFromTestCase(
                self.testcase_bad(count, name + 'Bad')
            )
        )



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fuzz testing')
    parser.add_argument('-c', '--count', type=int, default=100)
    parser.add_argument('-f', '--failfast', action='store_true')
    clargs = parser.parse_args()

    modules = []
    try:
        from . import pylibscrypt
        modules.append((pylibscrypt, 'pylibscrypt'))
    except ImportError:
        pass

    try:
        from . import pyscrypt
        modules.append((pyscrypt, 'pyscrypt'))
    except ImportError:
        pass

    try:
        from . import pylibsodium_salsa
        modules.append((pylibsodium_salsa, 'pylibsodium_salsa'))
    except ImportError:
        pass

    try:
        from . import pylibsodium
        modules.append((pylibsodium, 'pylibsodium'))
    except ImportError:
        pass

    try:
        from . import pypyscrypt_inline as pypyscrypt
        modules.append((pypyscrypt, 'pypyscrypt'))
    except ImportError:
        pass

    scrypt_args = (
        {'name':'password', 'type':'bytes'},
        {'name':'salt', 'type':'bytes'},
        {
            'name':'N', 'type':'int', 'opt':False,
            'valf':(lambda N=None: 2**rr(1,6) if N is None else
                    1 < N < 2**64 and not (N & (N - 1))),
            'skip':(lambda N: (N & (N - 1)) == 0 and N > 32 and N < 2**64)
        },
        {
            'name':'r', 'type':'int', 'opt':True,
            'valf':(lambda r=None: rr(1, 16) if r is None else 0<r<2**30),
            'skip':(lambda r: r > 16 and r < 2**30)
        },
        {
            'name':'p', 'type':'int', 'opt':True,
            'valf':(lambda p=None: rr(1, 16) if p is None else 0<p<2**30),
            'skip':(lambda p: p > 16 and p < 2**30)
        },
        {
            'name':'olen', 'type':'int', 'opt':True,
            'valf':(lambda l=None: rr(1, 1000) if l is None else l >= 0),
            'skip':(lambda l: l < 0 or l > 1024)
        },
    )

    scrypt_mcf_args = (
        {
            'name':'password', 'type':'bytes',
            'valf':(lambda p=None: Fuzzer.get_random_bytes(skip=0) if p is None
                    else not b'\0' in p)
        },
        {
            'name':'salt', 'type':'bytes', 'opt':False, 'none':True,
            'valf':(lambda s=None: Fuzzer.get_random_bytes((1,17)) if s is None
                    else 1 <= len(s) <= 16)
        },
        {
            'name':'N', 'type':'int', 'opt':False,
            'valf':(lambda N=None: 2**rr(1,6) if N is None else
                    1 < N < 2**64 and not (N & (N - 1))),
            'skip':(lambda N: (N & (N - 1)) == 0 and N > 32 and N < 2**64)
        },
        {
            'name':'r', 'type':'int', 'opt':True,
            'valf':(lambda r=None: rr(1, 16) if r is None else 0<r<2**30),
            'skip':(lambda r: r > 16 and r < 2**30)
        },
        {
            'name':'p', 'type':'int', 'opt':True,
            'valf':(lambda p=None: rr(1, 16) if p is None else 0<p<2**30),
            'skip':(lambda p: p > 16 and p < 2**30)
        },
        {
            'name':'prefix', 'type':'bytes', 'opt':True,
            'vals':(b'$s1$', b'$7$'),
            'skip':(lambda p: p is None)
        }
    )

    random.shuffle(modules)
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for m1, m2 in itertools.permutations(modules, 2):
        Fuzzer(
            m1[0].scrypt, scrypt_args, m2[0].scrypt,
            pass_good=lambda r1, r2, a: (
                isinstance(r1, bytes) and
                (r2 is None or r1 == r2) and
                (len(r1) == 64 if 'olen' not in a else len(r1) == a['olen'])
            )
        ).generate_tests(suite, clargs.count, m1[1])
        Fuzzer(
            m1[0].scrypt_mcf, scrypt_mcf_args, m2[0].scrypt_mcf,
            pass_good=lambda r1, r2, a: (
                m2[0].scrypt_mcf_check(r1, a['password']) and
                (r2 is None or m1[0].scrypt_mcf_check(r2, a['password'])) and
                (r2 is None or 'salt' not in a or a['salt'] is None or r1 == r2)
            )
        ).generate_tests(suite, clargs.count, m1[1])
    unittest.TextTestRunner(failfast=clargs.failfast).run(suite)

