'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.block import Block
from mock import Mock

raw_block = """Version: 1
Type: Block
Currency: zeta_brouzouf
Nonce: 45079
Number: 15
PoWMin: 4
Time: 1418083330
MedianTime: 1418080208
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
PreviousHash: 0000E73C340601ACA1AD5AAA5B5E56B03E178EF8
PreviousIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
MembersCount: 4
Identities:
Joiners:
Actives:
Leavers:
Excluded:
Certifications:
Transactions:
42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r
"""


raw_block_zero = """Version: 1
Type: Block
Currency: zeta_brouzouf
Nonce: 2125
Number: 0
PoWMin: 3
Time: 1418077277
MedianTime: 1418077277
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
Parameters: 0.01:302400:100:5259600:2629800:3:5:2629800:3:11:600:10:20:0.67
MembersCount: 4
Identities:
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:h/H8tDIEbfA4yxMQcvfOXVDQhi1sUa9qYtPKrM59Bulv97ouwbAvAsEkC1Uyit1IOpeAV+CQQs4IaAyjE8F1Cw==:1416335620:cgeek
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:lAW4mCPqA3cnEubHAGpMXR0o8euEdDVeSLplRgdLPf8Bty7R7FqVqwoAlL/4q/7p3O57Cz9z3mvhRSNwt23qBw==:1416378344:inso
RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:Ah55O8cvdkGS4at6AGOKUjy+wrFwAq8iKRJ5xLIb6Xdi3M8WfGOUdMjwZA6GlSkdtlMgEhQPm+r2PMebxKrCBg==:1416428323:vit
9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:ZjlNz2k/7Y38xwzaVEtyteOD12ukRT+x8NBFVTrcZtUHSJdqt7ejBAC0ULu7eCTLlmJk0jS6cuJ3IeVTLfFRDg==:1416436555:ManUtopiK
Joiners:
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:dkaXIiCYUJtCg8Feh/BKvPYf4uFH9CJ/zY6J4MlA9BsjmcMe4YAblvNt/gJy31b1aGq3ue3h14mLMCu84rraDg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416335620:cgeek
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:43FEO5wwKzo79k+WmZsrUDsNNceStYkrweEntwYGoGn9+YNjyyCbMmKcEU38xzMV2M0ZMgjvlTK30/vWwrD5CQ==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416378344:inso
RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:zPg1kgjVstsaKDBq3Re6Z84hlw0Ja2pjJEORmn7w5ifT6/e45BnEPJaqoVgImzSnytjOpzXN/rhAO4+UDJOUBQ==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416428323:vit
9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:ox/t5um2bbFJfc6NdRDM8DniGxlRB5zmKuW7WK+MiDpE32GUhf/tDcyfBkIpwIFcaY0hqLYW1OQlgbm2qT6xAw==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1416436555:ManUtopiK
Actives:
Leavers:
Excluded:
Certifications:
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:TgmDuMxZdyutroj9jiLJA8tQp/389JIzDKuxW5+h7GIfjDu1ZbwI7HNm5rlUDhR2KreaV/QJjEaItT4Cf75rCQ==
RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:xvIlhFdTUwqWx7XIG980xatL0JULOj1Ex15Q9nDcDLVtyFXZZCp1ZeRewkGjkJoGyOFGCJ1iDSB/qFzsPtrsDQ==
9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:mNsbLvezg8Zx1NPfs2gdGwmCKtoVWbw64yEHZE7uPkDvF+iexk93O8IT06HKgo1VI5SennwDfh0qp3Ko1OB5BQ==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:wIdLq6EYKSLoVXcXoSMLciBPMvJvvP1t5cTCIrvPH4qvo/y02al6vFfQR+wUGwFtoXulUSr8C+U1FRHWfUTCBg==
RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:Gr4EHqCEt+uuLbGPdu1qT/YObkqVthVzmFWCBlKRnRUz3xUt828W25GRtvdVn8hlycvCX/05mMlWeRMBUI/LDA==
9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:qn/XNJjaGIwfnR+wGrDME6YviCQbG+ywsQWnETlAsL6q7o3k1UhpR5ZTVY9dvejLKuC+1mUEXVTmH+8Ib55DBA==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:0:QLaYgLndAqRIk2uRAuxxhNUEQtSLpPqpfKvGBfClpQV0y7YTm1GnEoX9bY3DPhXU8GjUThngkFR0+M4Fx5R6DQ==
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:0:T+MkH18Eyddq5o93v2tSyBMd/RSkL/mcnE017t/t11QrMmFrXFZeufUhkVfRPi89kLSap4sLV/weEETXX8S7Aw==
9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:0:mWARDngVFmw76JPmHRZHUOh1MFjddNyJ3OMPQHMERFdeev1hKQ3pEUY9lQc6BL524GjIOcvLWufo65Ie0XTDCQ==
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:0:4vLU/VUE5VxcMnvv4mtJs9bky45o2fddKZCnP0FVGZD3BHC20YMPabTZ2RWcNiCc97zig1Munqj2Ss5RQMBDBA==
RdrHvL179Rw62UuyBrqy2M1crx7RPajaViBatS59EGS:9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:0:90w2HrbdsKIc6YJq3Ksa4sSgjpYSMM05+UuowAlYjrk1ixHIyWyg5odyZPRwO50aiIyUsbikoOWsMc3G8ob/Cg==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:9fx25FmeBDJcikZLWxK5HuzKNbY6MaWYXoK1ajteE42Y:0:28lv0p8EPHpVgAMiPvXvIe5lMvYJxwko2tv5bPO4voHRHSaDcTz5BR7Oe69S6wjANIEAMfebXiFMqZdj+mWRAA==
Transactions:
42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r
"""


class Test_Block:
    def test_fromraw(self):
        block = Block.from_signed_raw(raw_block)
        assert block.version == 1
        assert block.currency == "zeta_brouzouf"
        assert block.noonce == 45079
        assert block.number == 15
        assert block.powmin == 4
        assert block.time == 1418083330
        assert block.mediantime == 1418080208
        assert block.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert block.prev_hash == "0000E73C340601ACA1AD5AAA5B5E56B03E178EF8"
        assert block.prev_issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert block.members_count == 4
        assert block.identities == []
        assert block.joiners == []
        assert block.actives == []
        assert block.leavers == []
        assert block.excluded == []
        assert block.certifications == []
        assert block.transactions == []

    def test_from_signed_raw_block_zero(self):
        block = Block.from_signed_raw(raw_block_zero)
        assert block.version == 1
        assert block.currency == "zeta_brouzouf"
        assert block.noonce == 2125
        assert block.number == 0
        assert block.powmin == 3
        assert block.time == 1418077277
        assert block.mediantime == 1418077277
        assert block.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert block.parameters == ('0.01','302400','100','5259600','2629800','3','5',
                                    '2629800','3','11','600','10','20','0.67')
        assert block.members_count == 4
        assert len(block.identities) == 4
        assert len(block.joiners) == 4
        assert block.actives == []
        assert block.leavers == []
        assert block.excluded == []
        assert len(block.certifications) == 12
        assert block.transactions == []

    def test_toraw_fromsignedraw(self):
        block = Block.from_signed_raw(raw_block)
        rendered_raw = block.signed_raw()
        from_rendered_raw = Block.from_signed_raw(rendered_raw)

        assert from_rendered_raw.version == 1
        assert from_rendered_raw.currency == "zeta_brouzouf"
        assert from_rendered_raw.noonce == 45079
        assert from_rendered_raw.number == 15
        assert from_rendered_raw.powmin == 4
        assert from_rendered_raw.time == 1418083330
        assert from_rendered_raw.mediantime == 1418080208
        assert from_rendered_raw.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert from_rendered_raw.prev_hash == "0000E73C340601ACA1AD5AAA5B5E56B03E178EF8"
        assert from_rendered_raw.prev_issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert from_rendered_raw.members_count == 4
        assert from_rendered_raw.identities == []
        assert from_rendered_raw.joiners == []
        assert from_rendered_raw.actives == []
        assert from_rendered_raw.leavers == []
        assert from_rendered_raw.excluded == []
        assert from_rendered_raw.certifications == []
        assert from_rendered_raw.transactions == []

    def test_toraw_fromrawzero(self):
        block = Block.from_signed_raw(raw_block_zero)
        rendered_raw = block.signed_raw()
        from_rendered_raw = block.from_signed_raw(rendered_raw)

        assert from_rendered_raw.version == 1
        assert from_rendered_raw.currency == "zeta_brouzouf"
        assert from_rendered_raw.noonce == 2125
        assert from_rendered_raw.number == 0
        assert from_rendered_raw.powmin == 3
        assert from_rendered_raw.time == 1418077277
        assert from_rendered_raw.mediantime == 1418077277
        assert from_rendered_raw.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert from_rendered_raw.parameters == ('0.01','302400','100','5259600','2629800','3','5',
                                    '2629800','3','11','600','10','20','0.67')
        assert from_rendered_raw.members_count == 4
        assert len(from_rendered_raw.identities) == 4
        assert len(from_rendered_raw.joiners) == 4
        assert from_rendered_raw.actives == []
        assert from_rendered_raw.leavers == []
        assert from_rendered_raw.excluded == []
        assert len(from_rendered_raw.certifications) == 12
        assert from_rendered_raw.transactions == []


