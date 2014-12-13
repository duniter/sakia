'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.membership import Membership
from mock import Mock

inline_membership = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:\
dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==:\
0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416335620:cgeek\n"


class Test_Membership:
    def test_frominline(self):
        membership = Membership.from_inline(1, "zeta_brousouf", 'IN', inline_membership)

