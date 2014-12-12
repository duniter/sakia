'''
Created on 6 déc. 2014

@author: inso
'''

import pytest
from ucoinpy.documents.certification import SelfCertification
from mock import Mock

inline_selfcert = ""


class Test_SelfCertification:
    '''
    classdocs
    '''

    def test_certification(self):
        version = 1
        selfcert = SelfCertification.from_inline(version, inline_selfcert)
