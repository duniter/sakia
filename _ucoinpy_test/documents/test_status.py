'''
Created on 13 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.status import Status

raw_status = """Version: 1
Type: Status
Currency: beta_brousouf
Status: UP
Block: 8-1922C324ABC4AF7EF7656734A31F5197888DDD52
From: HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY
To: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==
"""


class Test_Status:
    def test_fromraw(self):
        status = Status.from_signed_raw(raw_status)
        assert status.status == 'UP'
        assert status.blockid == "8-1922C324ABC4AF7EF7656734A31F5197888DDD52"
        assert status.sender == "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY"
        assert status.recipient == "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        assert status.signatures[0] == "dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg=="

