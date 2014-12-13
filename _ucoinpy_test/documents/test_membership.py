'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.membership import Membership
from mock import Mock

membership_inline = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:\
dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==:\
0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416335620:cgeek\n"

membership_raw = """Version: 1
Type: Membership
Currency: beta_brousouf
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
Block: 0-DA39A3EE5E6B4B0D3255BFEF95601890AFD80709
Membership: IN
UserID: cgeek
CertTS: 1416335620
dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==
"""


class Test_Membership:
    def test_frominline(self):
        membership = Membership.from_inline(1, "zeta_brousouf", 'IN', membership_inline)
        assert membership.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert membership.block_number == 0
        assert membership.block_hash == "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
        assert membership.cert_ts == 1416335620
        assert membership.uid == "cgeek"
        assert membership.signatures[0] == "dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg=="
        assert membership.membership_type == 'IN'

    def test_fromraw(self):
        membership = Membership.from_signed_raw(membership_raw)
        assert membership.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert membership.block_number == 0
        assert membership.block_hash == "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
        assert membership.cert_ts == 1416335620
        assert membership.uid == "cgeek"
        assert membership.signatures[0] == "dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg=="
        assert membership.membership_type == 'IN'
