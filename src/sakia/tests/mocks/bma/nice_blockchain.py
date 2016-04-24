from ..server import MockServer
from duniterpy.api import errors

bma_lookup_john = {
    "partial": False,
    "results": [
        {
            "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
            "uids": [
                {
                    "uid": "john",
                    "meta": {
                        "timestamp": "0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
                    },
                    "revocation_sig": "CTmlh3tO4B8f8IbL8iDy5ZEr3jZDcxkPmDmRPQY74C39MRLXi0CKUP+oFzTZPYmyUC7fZrUXrb3LwRKWw1jEBQ==",
                    "revoked": False,
                    "self": "ZrHK0cCqrxWReROK0ciiSb45+dRphJa68qFaSjdve8bBdnGAu7+DIu0d+u/fXrNRXuObihOKMBIawaIVPNHqDw==",
                    "others": [
                        {
                            "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                            "meta": {
                                "block_number": 38580
                            },
                            "uids": [
                                "doe"
                            ],
                            "isMember": True,
                            "wasMember": True,
                            "signature": "4ulycI2MtBu/8bZipy+OsXDCNm9EyUIdZ1HA7hbJ66phKRNvv70Oo2YOF/+VDRJb97z9TqWKgfIQ0NbXU15xDg=="
                        },
                    ]
                }
            ],
            "signed": []
        }
    ]
}

bma_membership_john = {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "uid": "john",
    "sigDate": "0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "memberships":
        [
            {
                "version": 2,
                "currency": "test_currency",
                "membership": "IN",
                "blockNumber": 0,
                "blockHash": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                "written": 10000
            }
        ]
}

bma_lookup_doe = {
    "partial": False,
    "results": [
        {
            "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
            "uids": [
                {
                    "uid": "doe",
                    "meta": {
                        "timestamp": "0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
                    },
                    "revocation_sig": "CTmlh3tO4B8f8IbL8iDy5ZEr3jZDcxkPmDmRPQY74C39MRLXi0CKUP+oFzTZPYmyUC7fZrUXrb3LwRKWw1jEBQ==",
                    "revoked": False,
                    "self": "cIkHPQQ5+xTb4cKWv85rcYcZT+E3GDtX8B2nCK9Vs12p2Yz4bVaZiMvBBwisAAy2WBOaqHS3ydpXGtADchOICw==",
                    "others": []
                }
            ],
            "signed": [
                        {
                            "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                            "meta": {
                                "block_number": 38580
                            },
                            "uids": [
                                "john"
                            ],
                            "isMember": True,
                            "wasMember": True,
                            "signature": "4ulycI2MtBu/8bZipy+OsXDCNm9EyUIdZ1HA7hbJ66phKRNvv70Oo2YOF/+VDRJb97z9TqWKgfIQ0NbXU15xDg=="
                        },
                    ]
        }
    ]
}

bma_certifiers_of_john = {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "uid": "john",
    "isMember": True,
    "certifications": [
        {
            "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
            "uid": "doe",
            "isMember": True,
            "wasMember": True,
            "cert_time": {
                "block": 15,
                "medianTime": 1500000000
            },
            "sigDate": "101-BAD49448A1AD73C978CEDCB8F137D20A5715EBAA739DAEF76B1E28EE67B2C00C",
            "written": {
                "number": 15,
                "hash": "0000EC88BBBAA29D530D2B815DEE264DDC9F07F4"
            },
            "signature": "oliiPDhniZAGHrIFL66oHR+cqD4aTgXX+20VFLMfNHwdYPeik76hy334zxhoDC4cPODMb9df2nF/EDfCefrNBg=="
        },
    ]
}

bma_certified_by_john = {
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "uid": "john",
    "isMember": True,
    "wasMember": False,
    "certifications": [
    ]
}

bma_certified_by_doe = {
    "pubkey": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
    "uid": "doe",
    "isMember": True,
    "certifications": [
        {
            "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
            "uid": "john",
            "isMember": True,
            "wasMember": True,
            "cert_time": {
                "block": 15,
                "medianTime": 1500000000
            },
            "sigDate": "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            "written": {
                "number": 15,
                "hash": "0000EC88BBBAA29D530D2B815DEE264DDC9F07F4"
            },
            "signature": "oliiPDhniZAGHrIFL66oHR+cqD4aTgXX+20VFLMfNHwdYPeik76hy334zxhoDC4cPODMb9df2nF/EDfCefrNBg=="
        },
    ]
}

bma_parameters = {
    "currency": "test_currency",
    "c": 0.1,
    "dt": 86400,
    "ud0": 100,
    "sigPeriod": 600,
    "sigValidity": 2629800,
    "sigQty": 3,
    "xpercent": 0.9,
    "sigStock": 10,
    "sigWindow": 1000,
    "msValidity": 2629800,
    "stepMax": 3,
    "medianTimeBlocks": 11,
    "avgGenTime": 600,
    "dtDiffEval": 20,
    "blocksRot": 144,
    "percentRot": 0.67
}

bma_blockchain_0 = {
    "version": 2,
    "nonce": 10144,
    "number": 0,
    "powMin": 3,
    "time": 1421838980,
    "medianTime": 1421838980,
    "membersCount": 4,
    "monetaryMass": 0,
    "currency": "test_currency",
    "issuer": "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
    "signature": "+78w7251vvRdhoIJ6IWHEiEOLxNrmfQf45Y5sYvPdnAdXkVpO1unMV5YA/G5Vhphyz1dICrbeKCPM5qbFsoWAQ==",
    "hash": "00063EB6E83F8717CEF1D25B3E2EE308374A14B1",
    "inner_hash": "00063EB6E83F8717CEF1D25B3E2EE308374A14B1",
    "parameters": "0.1:86400:100:604800:2629800:3:3:2629800:3:11:600:20:144:0.67",
    "previousHash": None,
    "previousIssuer": None,
    "dividend": None,
    "membersChanges": [],
    "identities": [
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:inso",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:cgeek",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:moul",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:galuel"
    ],
    "joiners": [
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:inso",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:cgeek",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:moul",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:galuel"
    ],
    "actives": [],
    "leavers": [],
    "revoked": [],
    "excluded": [],
    "certifications": [
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:3wmCVW8AbVxRFm2PuLXD9UTCIg93MhUblZJvlYrDldSV4xuA7mZCd8TV4vb/6Bkc0FMQgBdHtpXrQ7dpo20uBA==",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:7UMQsUjLvuiZKIzOH5rrZDdDi5rXUo69EuQulY1Zm42xpRx/Gt5CkoTcJ/Mu83oElQbcZZTz/lVJ6IS0jzMiCQ==",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:twWSY9etI82FLEHzhdqIoHsC9ehWCA7DCPiGxDLCWGPO4TG77hwtn3RcC68qoKHCib577JCp+fcKyp2vyI6FDA==",
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:7K5MHkO8ibf5SchmPkRrmsg9owEZZ23uEMJJSQYG7L3PUmAKmmV/0VSjivxXH8gJGQBGsXQoK79x1jsYnj2nAg==",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:Jua4FcEJFptSE5OoG1/Mgzx4e9jgGnYu7t8g1sqqPujI9hRhLFNXbQXedPS1q1OD5vWivA045gKOq/gnj8opDg==",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:R/DV4/wYjvBG09QSOGtnxd3bfPFhVjEE5Uy3BsBMVUvjLsgxjf8NgLhYVozcHTRWS43ArxlXKfS5m3+KIPhhAQ==",
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:4hP+ahJK021akL4UxB6c5QLaGJXa9eapd3nfdFQe+Xy87f/XLhj8BCa22XbbOlyGdaZRT3AYzbCL2UD5tI8mCw==",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:sZTQJr0d/xQnxrIIdSePUJpSTOa8v6IYGXMF2fVDZxQU8vwfzPm2dUKTaF0nU6E9wOYszzkBHaXL85nir+WtCQ==",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:hDuBkoFhWhR/FgOU1+9SbQGBMIr47xqUzw1ZMERaPQo4aWm0WFbZurG4lvuJZzTyG6RF/gSw4VPvYZFPxWmADg==",
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:79ZVrBehElVZh82fJdR18IJx06GkEVZTbwdHH4zb0S6VaGwdtLh1rvomm4ukBvUc8r/suTweG/SScsJairXNAg==",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:e/ai9E4G5CFB9Qi329e0ffYpZMgxj8mM4rviqIr2+UESA0UG86OuAAyHO11hYeyolZRiU8I7WdtNE98B1uZuBg==",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:q4PCneYkcPH8AHEqEvqTtYQWslhlYO2B87aReuOl1uPczn5Q3VkZFAsU48ZTYryeyWp2nxdQojdFYhlAUNchAw=="
    ],
    "transactions": [],
    "raw": """Version: 2
Type: Block
Currency: test_currency
Number: 0
PoWMin: 3
Time: 1421838980
MedianTime: 1421838980
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
Parameters: 0.1:86400:100:604800:15:604800:2629800:3:0.9:2629800:3:11:600:20:144:0.67
MembersCount: 4
Identities:
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:inso
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:cgeek
BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:moul
37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:galuel
Joiners:
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:inso
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:cgeek
BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:moul
37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:galuel
Actives:
Leavers:
Revoked:
Excluded:
Certifications:
37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:3wmCVW8AbVxRFm2PuLXD9UTCIg93MhUblZJvlYrDldSV4xuA7mZCd8TV4vb/6Bkc0FMQgBdHtpXrQ7dpo20uBA==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:7UMQsUjLvuiZKIzOH5rrZDdDi5rXUo69EuQulY1Zm42xpRx/Gt5CkoTcJ/Mu83oElQbcZZTz/lVJ6IS0jzMiCQ==
BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:twWSY9etI82FLEHzhdqIoHsC9ehWCA7DCPiGxDLCWGPO4TG77hwtn3RcC68qoKHCib577JCp+fcKyp2vyI6FDA==
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:7K5MHkO8ibf5SchmPkRrmsg9owEZZ23uEMJJSQYG7L3PUmAKmmV/0VSjivxXH8gJGQBGsXQoK79x1jsYnj2nAg==
BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:Jua4FcEJFptSE5OoG1/Mgzx4e9jgGnYu7t8g1sqqPujI9hRhLFNXbQXedPS1q1OD5vWivA045gKOq/gnj8opDg==
37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:R/DV4/wYjvBG09QSOGtnxd3bfPFhVjEE5Uy3BsBMVUvjLsgxjf8NgLhYVozcHTRWS43ArxlXKfS5m3+KIPhhAQ==
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:4hP+ahJK021akL4UxB6c5QLaGJXa9eapd3nfdFQe+Xy87f/XLhj8BCa22XbbOlyGdaZRT3AYzbCL2UD5tI8mCw==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:sZTQJr0d/xQnxrIIdSePUJpSTOa8v6IYGXMF2fVDZxQU8vwfzPm2dUKTaF0nU6E9wOYszzkBHaXL85nir+WtCQ==
37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:hDuBkoFhWhR/FgOU1+9SbQGBMIr47xqUzw1ZMERaPQo4aWm0WFbZurG4lvuJZzTyG6RF/gSw4VPvYZFPxWmADg==
8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:79ZVrBehElVZh82fJdR18IJx06GkEVZTbwdHH4zb0S6VaGwdtLh1rvomm4ukBvUc8r/suTweG/SScsJairXNAg==
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:e/ai9E4G5CFB9Qi329e0ffYpZMgxj8mM4rviqIr2+UESA0UG86OuAAyHO11hYeyolZRiU8I7WdtNE98B1uZuBg==
BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:q4PCneYkcPH8AHEqEvqTtYQWslhlYO2B87aReuOl1uPczn5Q3VkZFAsU48ZTYryeyWp2nxdQojdFYhlAUNchAw==
Transactions:
InnerHash: 09500111588846873CA0110602DDC17FB34AA9F4548B7CE322C845902FFC1429
Nonce: 10144
"""
}

bma_blockchain_current = {
    "version": 2,
    "nonce": 6909,
    "number": 15,
    "powMin": 4,
    "time": 1441618206,
    "medianTime": 1441614759,
    "membersCount": 20,
    "monetaryMass": 11711349901120,
    "currency": "test_currency",
    "issuer": "EPs9qX7HmCDy6ptUoMLpTzbh9toHu4au488pBTU9DN6y",
    "signature": "kz/34w1cG+8tYacuPXf3FPmsFwrvtWkwp1POLJuX1P0zYaB9Tuu7iyYJzMQS0Xa3vwuWRqfz+fgyoCGnBjBLBQ==",
    "hash": "0000CB4E9CCDE6F579135331C97F13903E8B6E21",
    "parameters": "",
    "previousHash": "00003BDA844D77EEE7CF32A6C3C87F2ACBFCFCBB",
    "previousIssuer": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
    "dividend": None,
    "membersChanges": [],
    "identities": [],
    "joiners": [],
    "actives": [],
    "leavers": [],
    "excluded": [],
    "certifications": [],
    "transactions": [],
    "raw": """Version: 2
Type: Block
Currency: meta_brouzouf
Number: 30898
PoWMin: 4
Time: 1441618206
MedianTime: 1441614759
Issuer: EPs9qX7HmCDy6ptUoMLpTzbh9toHu4au488pBTU9DN6y
PreviousHash: 00003BDA844D77EEE7CF32A6C3C87F2ACBFCFCBB
PreviousIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
MembersCount: 20
Identities:
Joiners:
Actives:
Leavers:
Revoked:
Excluded:
Certifications:
Transactions:
InnerHash: 6BB2E0BE18BEA428379336FB5F09DCE0EB594D09CDD705085CA91AA966C27CFA
Nonce: 6909
"""
}

# Sent 6, received 20 + 30
bma_txhistory_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "history":
        {
            "sent":
                [
                    {
                        "version": 2,
                        "issuers":
                            [
                                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
                            ],
                        "inputs":
                            [
                                "D:7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:8"
                            ],
                        "unlocks":
                            [
                                "SIG(0)"
                            ],
                        "outputs":
                            [
                                "2:1:SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)",
                                "6:1:SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)"
                            ],
                        "comment": "",
                        "signatures":
                            [
                                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
                            ],
                        "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
                        "block_number": 2,
                        "time": 1421932545
                    },
                ],
            "received":
                [
                    {
                        "version": 2,
                        "issuers":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                            ],
                        "inputs":
                            [
                                "D:FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:8"
                            ],
                        "unlocks":
                            [
                                "SIG(0)"
                            ],
                        "outputs":
                            [
                                "2:1:SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)",
                                "6:1:SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)"
                            ],
                        "comment": "",
                        "signatures":
                            [
                                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
                            ],
                        "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
                        "block_number": 2,
                        "time": 1421932545
                    },
                    {
                        "version": 2,
                        "issuers":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                            ],
                        "inputs":
                            [
                                "D:FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:8"
                            ],
                        "unlocks":
                            [
                                "SIG(0)"
                            ],
                        "outputs":
                            [
                                "5:1:SIG(FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn)",
                                "40:1:SIG(7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ)"
                            ],
                        "comment": "",
                        "signatures":
                            [
                                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
                            ],
                        "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
                        "block_number": 2,
                        "time": 1421932545
                    },
                ],
            "sending": [],
            "receiving": []
        }
}

bma_udhistory_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "history":
        {
            "history":
                [
                    {
                        "block_number": 2,
                        "consumed": False,
                        "time": 1435749971,
                        "amount": 5,
                        "base": 1
                    },
                    {
                        "block_number": 10,
                        "consumed": False,
                        "time": 1435836032,
                        "amount": 10,
                        "base": 1
                    }
                ]
        }}

bma_txsources_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "sources":
        [
            {
                "type": "D",
                "noffset": 2,
                "identifier": "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                "amount": 70,
                "base": 0
            },
            {
                "type": "D",
                "noffset": 4,
                "identifier": "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                "amount": 90,
                "base": 0
            }
        ]}

bma_with_ud = {
    "result":
        {
            "blocks": []
        }
}


def get_mock(loop):
    mock = MockServer(loop)

    mock.add_route('GET', '/blockchain/parameters', bma_parameters, 200)

    mock.add_route('GET', '/blockchain/with/[UD|ud]', bma_with_ud, 200)

    mock.add_route('GET', '/blockchain/current', bma_blockchain_current, 200)

    mock.add_route('GET', '/blockchain/block/0', bma_blockchain_0, 200)

    mock.add_route('GET', '/blockchain/block/15', bma_blockchain_current, 200)

    mock.add_route('GET', '/tx/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ/blocks/0/99', bma_txhistory_john,
                   200)

    mock.add_route('GET', '/tx/sources/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_txsources_john, 200)

    mock.add_route('GET', '/ud/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_udhistory_john, 200)

    mock.add_route('GET', '/wot/certifiers-of/john', bma_certifiers_of_john,
                   200)

    mock.add_route('GET', '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_certifiers_of_john,
                   200)

    mock.add_route('GET', '/wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_certified_by_john, 200)

    mock.add_route('GET', '/wot/lookup/john', bma_lookup_john, 200)

    mock.add_route('GET', '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_lookup_john, 200)

    mock.add_route('GET', '/wot/lookup/doe', bma_lookup_doe, 200)

    mock.add_route('GET', '/wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn', bma_lookup_doe, 200)

    mock.add_route('GET', '/blockchain/memberships/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_membership_john,
                   200)

    mock.add_route('GET', '/wot/lookup/wrong_pubkey',
                   {'ucode': errors.NO_MATCHING_IDENTITY, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/wrong_pubkey',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/lookup/wrong_uid',
                   {'ucode': errors.NO_MATCHING_IDENTITY, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/wrong_uid',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/wot/certifiers-of/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('GET', '/blockchain/memberships/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn',
                   {'ucode': errors.NO_MEMBER_MATCHING_PUB_OR_UID, 'message': "No member matching this pubkey or uid"}, 404)

    mock.add_route('POST', '/tx/process', {}, 200, )

    return mock
