'''
Created on 6 déc. 2014

@author: inso
'''

import pytest
from ucoinpy.documents.certification import SelfCertification, Certification
from mock import Mock

selfcert_inlines = ["HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:\
h/H8tDIEbfA4yxMQcvfOXVDQhi1sUa9qYtPKrM59Bulv97ouwbAvAsEkC1Uyit1IOpeAV+CQQs4IaAyjE8F1Cw==:\
1416335620:cgeek\n", "RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:\
Ah55O8cvdkGS4at6AGOKUjy+wrFwAq8iKRJ5xLIb6Xdi3M8WfGOUdMjwZA6GlSkdtlMgEhQPm+r2PMebxKrCBg==:\
1416428323:vit\n" ]

cert_inlines = [
"8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:\
0:TgmDuMxZdyutroj9jiLJA8tQp/389JIzDKuxW5+h7GIfjDu1ZbwI7HNm5rlUDhR2KreaV/QJjEaItT4Cf75rCQ==\n",
"9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:\
qn/XNJjaGIwfnR+wGrDME6YviCQbG+ywsQWnETlAsL6q7o3k1UhpR5ZTVY9dvejLKuC+1mUEXVTmH+8Ib55DBA==\n"
]

class Test_SelfCertification:
    '''
    classdocs
    '''

    def test_selfcertification(self):
        version = 1
        currency = "zeta_brousouf"
        selfcert = SelfCertification.from_inline(version, currency, selfcert_inlines[0])
        assert selfcert.pubkey == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert selfcert.signatures[0] == "h/H8tDIEbfA4yxMQcvfOXVDQhi1sUa9qYtPKrM59Bulv97ouwbAvAsEkC1Uyit1IOpeAV+CQQs4IaAyjE8F1Cw=="
        assert selfcert.timestamp == 1416335620
        assert selfcert.identifier == "cgeek"

        selfcert = SelfCertification.from_inline(version, currency, selfcert_inlines[1])
        assert selfcert.pubkey == "RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS"
        assert selfcert.signatures[0] == "Ah55O8cvdkGS4at6AGOKUjy+wrFwAq8iKRJ5xLIb6Xdi3M8WfGOUdMjwZA6GlSkdtlMgEhQPm+r2PMebxKrCBg=="
        assert selfcert.timestamp == 1416428323
        assert selfcert.identifier == "vit"

    def test_certifications(self):
        version = 1
        currency = "zeta_brousouf"
        blockhash = "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
        cert = Certification.from_inline(version, currency, blockhash, cert_inlines[0])
        assert cert.pubkey_from == "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        assert cert.pubkey_to == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert cert.blocknumber == 0
        assert cert.blockhash == blockhash
        assert cert.signatures[0] == "TgmDuMxZdyutroj9jiLJA8tQp/389JIzDKuxW5+h7GIfjDu1ZbwI7HNm5rlUDhR2KreaV/QJjEaItT4Cf75rCQ=="

        cert = Certification.from_inline(version, currency, blockhash, cert_inlines[1])
        assert cert.pubkey_from == "9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y"
        assert cert.pubkey_to == "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        assert cert.blocknumber == 0
        assert cert.blockhash == blockhash
        assert cert.signatures[0] == "qn/XNJjaGIwfnR+wGrDME6YviCQbG+ywsQWnETlAsL6q7o3k1UhpR5ZTVY9dvejLKuC+1mUEXVTmH+8Ib55DBA=="



