from ..server import MockServer

bma_lookup_john = {
    "partial": False,
    "results": [
        {
            "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
            "uids": [
                {
                    "uid": "john",
                    "meta": {
                        "timestamp": 1441130831
                    },
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
    "uid": "inso",
    "sigDate": 1441130831,
    "memberships":
        [
            {

                "version": 1,
                "currency": "test_currency",
                "membership": "IN",
                "blockNumber": 0,
                "blockHash": "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
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
                        "timestamp": 1441130831
                    },
                    "self": "cIkHPQQ5+xTb4cKWv85rcYcZT+E3GDtX8B2nCK9Vs12p2Yz4bVaZiMvBBwisAAy2WBOaqHS3ydpXGtADchOICw==",
                    "others": []
                }
            ],
            "signed": []
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
            "medianTime": 1447693329
          },
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
    "certifications": [
    ]
}

bma_parameters = {
    "currency": "test_currency",
    "c": 0.1,
    "dt": 86400,
    "ud0": 100,
    "sigDelay": 604800,
    "sigValidity": 2629800,
    "sigQty": 3,
    "sigWoT": 3,
    "msValidity": 2629800,
    "stepMax": 3,
    "medianTimeBlocks": 11,
    "avgGenTime": 600,
    "dtDiffEval": 20,
    "blocksRot": 144,
    "percentRot": 0.67
}

bma_blockchain_0 = {
    "version": 1,
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
    "parameters": "0.1:86400:100:604800:2629800:3:3:2629800:3:11:600:20:144:0.67",
    "previousHash": None,
    "previousIssuer": None,
    "dividend": None,
    "membersChanges": [],
    "identities": [
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:1421787800:inso",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:1421786393:cgeek",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:1421790376:moul",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:1421787461:galuel"
    ],
    "joiners": [
        "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787800:inso",
        "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421786393:cgeek",
        "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421790376:moul",
        "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787461:galuel"
    ],
    "actives": [],
    "leavers": [],
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
    "raw": "Version: 1\nType: Block\nCurrency: test_currency\nNonce: 10144\nNumber: 0\nPoWMin: 3\nTime: 1421838980\nMedianTime: 1421838980\nIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nParameters: 0.1:86400:100:604800:2629800:3:3:2629800:3:11:600:20:144:0.67\nMembersCount: 4\nIdentities:\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:1421787800:inso\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:1421786393:cgeek\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:1421790376:moul\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:1421787461:galuel\nJoiners:\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787800:inso\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421786393:cgeek\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421790376:moul\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787461:galuel\nActives:\nLeavers:\nExcluded:\nCertifications:\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:3wmCVW8AbVxRFm2PuLXD9UTCIg93MhUblZJvlYrDldSV4xuA7mZCd8TV4vb/6Bkc0FMQgBdHtpXrQ7dpo20uBA==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:7UMQsUjLvuiZKIzOH5rrZDdDi5rXUo69EuQulY1Zm42xpRx/Gt5CkoTcJ/Mu83oElQbcZZTz/lVJ6IS0jzMiCQ==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:twWSY9etI82FLEHzhdqIoHsC9ehWCA7DCPiGxDLCWGPO4TG77hwtn3RcC68qoKHCib577JCp+fcKyp2vyI6FDA==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:7K5MHkO8ibf5SchmPkRrmsg9owEZZ23uEMJJSQYG7L3PUmAKmmV/0VSjivxXH8gJGQBGsXQoK79x1jsYnj2nAg==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:Jua4FcEJFptSE5OoG1/Mgzx4e9jgGnYu7t8g1sqqPujI9hRhLFNXbQXedPS1q1OD5vWivA045gKOq/gnj8opDg==\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:R/DV4/wYjvBG09QSOGtnxd3bfPFhVjEE5Uy3BsBMVUvjLsgxjf8NgLhYVozcHTRWS43ArxlXKfS5m3+KIPhhAQ==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:4hP+ahJK021akL4UxB6c5QLaGJXa9eapd3nfdFQe+Xy87f/XLhj8BCa22XbbOlyGdaZRT3AYzbCL2UD5tI8mCw==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:sZTQJr0d/xQnxrIIdSePUJpSTOa8v6IYGXMF2fVDZxQU8vwfzPm2dUKTaF0nU6E9wOYszzkBHaXL85nir+WtCQ==\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:hDuBkoFhWhR/FgOU1+9SbQGBMIr47xqUzw1ZMERaPQo4aWm0WFbZurG4lvuJZzTyG6RF/gSw4VPvYZFPxWmADg==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:79ZVrBehElVZh82fJdR18IJx06GkEVZTbwdHH4zb0S6VaGwdtLh1rvomm4ukBvUc8r/suTweG/SScsJairXNAg==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:e/ai9E4G5CFB9Qi329e0ffYpZMgxj8mM4rviqIr2+UESA0UG86OuAAyHO11hYeyolZRiU8I7WdtNE98B1uZuBg==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:q4PCneYkcPH8AHEqEvqTtYQWslhlYO2B87aReuOl1uPczn5Q3VkZFAsU48ZTYryeyWp2nxdQojdFYhlAUNchAw==\nTransactions:\n"
}

bma_blockchain_current = {
    "version": 1,
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
    "raw": "Version: 1\nType: Block\nCurrency: meta_brouzouf\nNonce: 6909\nNumber: 30898\nPoWMin: 4\nTime: 1441618206\nMedianTime: 1441614759\nIssuer: EPs9qX7HmCDy6ptUoMLpTzbh9toHu4au488pBTU9DN6y\nPreviousHash: 00003BDA844D77EEE7CF32A6C3C87F2ACBFCFCBB\nPreviousIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nMembersCount: 20\nIdentities:\nJoiners:\nActives:\nLeavers:\nExcluded:\nCertifications:\nTransactions:\n"
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
                        "version": 1,
                        "issuers":
                            [
                                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
                            ],
                        "inputs":
                            [
                                "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
                            ],
                        "outputs":
                            [
                                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:2",
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:6"
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
                        "version": 1,
                        "issuers":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                            ],
                        "inputs":
                            [
                                "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
                            ],
                        "outputs":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:2",
                                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:20"
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
                        "version": 1,
                        "issuers":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                            ],
                        "inputs":
                            [
                                "0:D:1:000A8362AE0C1B8045569CE07735DE4C18E81586:8"
                            ],
                        "outputs":
                            [
                                "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn:5",
                                "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ:40"
                            ],
                        "comment": "",
                        "signatures":
                            [
                                "1Mn8q3K7N+R4GZEpAUm+XSyty1Uu+BuOy5t7BIRqgZcKqiaxfhAUfDBOcuk2i4TJy1oA5Rntby8hDN+cUCpvDg=="
                            ],
                        "hash": "5FB3CB80A982E2BDFBB3EA94673A74763F58CB2A",
                        "block_number": 12,
                        "time": 1421932454
                    }
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
                        "amount": 5
                    },
                    {

                        "block_number": 10,
                        "consumed": False,
                        "time": 1435836032,
                        "amount": 10

                    }
                ]
        }}

bma_txsources_john = {
    "currency": "test_currency",
    "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
    "sources":
        [
            {
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "number": 2,
                "fingerprint": "4A317E3D676E9800E1E92AA2A7255BCEEFF31185",
                "amount": 7
            },
            {
                "pubkey": "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                "type": "D",
                "number": 4,
                "fingerprint": "4A317E3D676E9800E1E92AA2A7255BCEEFF31185",
                "amount": 9
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

    mock.add_route('GET', '/tx/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ/blocks/0/99', bma_txhistory_john, 200)

    mock.add_route('GET', '/tx/sources/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_txsources_john, 200)

    mock.add_route('GET', '/ud/history/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_udhistory_john, 200)

    mock.add_route('GET', '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_certifiers_of_john, 200)

    mock.add_route('GET', '/wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_certified_by_john, 200)

    mock.add_route('GET', '/wot/lookup/john', bma_lookup_john, 200)

    mock.add_route('GET', '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ', bma_lookup_john, 200)

    mock.add_route('GET', '/wot/lookup/doe', bma_lookup_doe, 200)

    mock.add_route('GET', '/wot/lookup/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn',bma_lookup_doe,200)

    mock.add_route('GET', '/blockchain/memberships/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ',bma_membership_john,200)

    mock.add_route('GET', '/wot/certifiers-of/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn',
                   {'error':"No member matching this pubkey or uid"},404)

    mock.add_route('GET', '/blockchain/memberships/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn',
                   {'error':"No member matching this pubkey or uid"}, 404)

    mock.add_route('POST', '/tx/process', {},200,)

    return mock
