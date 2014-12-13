'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.transaction import Transaction
from mock import Mock


compact_transaction = """TX:1:1:3:1:0
HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY
0:T:65:D717FEC1993554F8EAE4CEA88DE5FBB6887CFAE8:4
0:T:77:F80993776FB55154A60B3E58910C942A347964AD:15
0:D:88:F4A47E39BC2A20EE69DCD5CAB0A9EB3C92FD8F7B:11
BYfWYFrsyjpvpFysgu19rGK3VHBkz4MqmQbNyEuVU64g:30
42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r
"""


class Test_Transaction:
    def test_fromraw(self):
        tx = Transaction.from_compact("zeta_brousouf", 2, compact_transaction)
        assert tx.version == 1
        assert len(tx.issuers) == 1
        assert len(tx.inputs) == 3
        assert len(tx.outputs) == 1

        assert tx.issuers[0] == "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY"

        assert tx.inputs[0].index == 0
        assert tx.inputs[0].source == 'T'
        assert tx.inputs[0].number == 65
        assert tx.inputs[0].txhash == "D717FEC1993554F8EAE4CEA88DE5FBB6887CFAE8"
        assert tx.inputs[0].amount == 4

        assert tx.inputs[1].index == 0
        assert tx.inputs[1].source == 'T'
        assert tx.inputs[1].number == 77
        assert tx.inputs[1].txhash == "F80993776FB55154A60B3E58910C942A347964AD"
        assert tx.inputs[1].amount == 15

        assert tx.inputs[2].index == 0
        assert tx.inputs[2].source == 'D'
        assert tx.inputs[2].number == 88
        assert tx.inputs[2].txhash == "F4A47E39BC2A20EE69DCD5CAB0A9EB3C92FD8F7B"
        assert tx.inputs[2].amount == 11

        assert tx.outputs[0].pubkey == "BYfWYFrsyjpvpFysgu19rGK3VHBkz4MqmQbNyEuVU64g"
        assert tx.outputs[0].amount == 30
