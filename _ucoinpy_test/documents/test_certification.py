'''
Created on 6 déc. 2014

@author: inso
'''

import pytest
from ucoinpy.documents.certification import SelfCertification
from ucoinpy.key import Base58Encoder
from mock import Mock

from nacl.signing import SigningKey

uid = "lolcat"
timestamp = 1409990782.24
correct_certification = """UID:lolcat
META:TS:1409990782
J3G9oM5AKYZNLAB5Wx499w61NuUoS57JVccTShUbGpCMjCqj9yXXqNq7dyZpDWA6BxipsiaMZhujMeBfCznzyci
"""

key = SigningKey()


class Test_SelfCertification:
    '''
    classdocs
    '''

    def test_certification(self):
        cert = SelfCertification(timestamp, uid)
        assert cert.signed(key) == correct_certification
