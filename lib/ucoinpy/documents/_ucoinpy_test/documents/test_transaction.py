'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.transaction import Transaction
from mock import Mock


tx_compact = """TX:1:1:3:1:0
HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY
0:T:65:D717FEC1993554F8EAE4CEA88DE5FBB6887CFAE8:4
0:T:77:F80993776FB55154A60B3E58910C942A347964AD:15
0:D:88:F4A47E39BC2A20EE69DCD5CAB0A9EB3C92FD8F7B:11
BYfWYFrsyjpvpFysgu19rGK3VHBkz4MqmQbNyEuVU64g:30
42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r
"""

tx_raw = """Version: 1
Type: Transaction
Currency: beta_brousouf
Issuers:
HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY
Inputs:
0:T:65:D717FEC1993554F8EAE4CEA88DE5FBB6887CFAE8:4
0:T:77:F80993776FB55154A60B3E58910C942A347964AD:15
0:D:88:F4A47E39BC2A20EE69DCD5CAB0A9EB3C92FD8F7B:11
Outputs:
BYfWYFrsyjpvpFysgu19rGK3VHBkz4MqmQbNyEuVU64g:30
Comment:
42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r
"""


class Test_Transaction:
    def test_fromcompact(self):
        tx = Transaction.from_compact("zeta_brousouf", tx_compact)
        assert tx.version == 1
        assert tx.currency == "zeta_brousouf"
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

        assert tx.signatures[0] == "42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r"

    def test_fromraw(self):
        tx = Transaction.from_signed_raw(tx_raw)
        assert tx.version == 1
        assert tx.currency == "beta_brousouf"
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

        assert tx.signatures[0] == "42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r"

    def test_fromraw_toraw(self):
        tx = Transaction.from_signed_raw(tx_raw)
        rendered_tx = tx.signed_raw()
        from_rendered_tx = Transaction.from_signed_raw(rendered_tx)

        assert from_rendered_tx.version == 1
        assert len(from_rendered_tx.issuers) == 1
        assert len(from_rendered_tx.inputs) == 3
        assert len(from_rendered_tx.outputs) == 1

        assert from_rendered_tx.issuers[0] == "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY"

        assert from_rendered_tx.inputs[0].index == 0
        assert from_rendered_tx.inputs[0].source == 'T'
        assert from_rendered_tx.inputs[0].number == 65
        assert from_rendered_tx.inputs[0].txhash == "D717FEC1993554F8EAE4CEA88DE5FBB6887CFAE8"
        assert from_rendered_tx.inputs[0].amount == 4

        assert from_rendered_tx.inputs[1].index == 0
        assert from_rendered_tx.inputs[1].source == 'T'
        assert from_rendered_tx.inputs[1].number == 77
        assert from_rendered_tx.inputs[1].txhash == "F80993776FB55154A60B3E58910C942A347964AD"
        assert from_rendered_tx.inputs[1].amount == 15

        assert from_rendered_tx.inputs[2].index == 0
        assert from_rendered_tx.inputs[2].source == 'D'
        assert from_rendered_tx.inputs[2].number == 88
        assert from_rendered_tx.inputs[2].txhash == "F4A47E39BC2A20EE69DCD5CAB0A9EB3C92FD8F7B"
        assert from_rendered_tx.inputs[2].amount == 11

        assert from_rendered_tx.outputs[0].pubkey == "BYfWYFrsyjpvpFysgu19rGK3VHBkz4MqmQbNyEuVU64g"
        assert from_rendered_tx.outputs[0].amount == 30

        assert from_rendered_tx.signatures[0] == "42yQm4hGTJYWkPg39hQAUgP6S6EQ4vTfXdJuxKEHL1ih6YHiDL2hcwrFgBHjXLRgxRhj2VNVqqc6b4JayKqTE14r"

