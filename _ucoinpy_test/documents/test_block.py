'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.block import Block
from mock import Mock

raw_block = "Version: 1\nType: \
Block\nCurrency: zeta_brouzouf\n\
Nonce: 45079\nNumber: 15\nPoWMin: 4\n\
Time: 1418083330\nMedianTime: 1418080208\n\
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\n\
PreviousHash: 0000E73C340601ACA1AD5AAA5B5E56B03E178EF8\n\
PreviousIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\n\
MembersCount: 4\nIdentities:\nJoiners:\nActives:\nLeavers:\n\
Excluded:\nCertifications:\nTransactions:\n"


class Test_Block:
    def test_fromraw(self):
        block = Block.from_raw(raw_block)
        assert block.version == 1
        assert block.currency == "zeta_brouzouf"
        assert block.noonce == 45079
        assert block.number == 15
        assert block.powmin == 4
        assert block.time == 1418083330
        assert block.mediantime == 1418080208
        assert block.issuer == "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        assert block.previoushash == "0000E73C340601ACA1AD5AAA5B5E56B03E178EF8"
        assert block.previousissuer == "0000E73C340601ACA1AD5AAA5B5E56B03E178EF8"
        assert block.memberscount == 4
        assert block.identities == []
        assert block.joiners == []
        assert block.actives == []
        assert block.leavers == []
        assert block.excluded == []
        assert block.certifications == []
        assert block.transactions == []
