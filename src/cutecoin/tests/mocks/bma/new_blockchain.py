from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER

bma_block_0 = b"""{
    "version": 1,
    "nonce": 10144,
    "number": 0,
    "powMin": 3,
    "time": 1421838980,
    "medianTime": 1421838980,
    "membersCount": 4,
    "monetaryMass": 0,
    "currency": "meta_brouzouf",
    "issuer": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
    "signature": "+78w7251vvRdhoIJ6IWHEiEOLxNrmfQf45Y5sYvPdnAdXkVpO1unMV5YA/G5Vhphyz1dICrbeKCPM5qbFsoWAQ==",
    "hash": "00063EB6E83F8717CEF1D25B3E2EE308374A14B1",
    "parameters": "0.1:86400:100:604800:2629800:3:3:2629800:3:11:600:20:144:0.67",
    "previousHash": null,
    "previousIssuer": null,
    "dividend": null,
    "membersChanges": [ ],
    "identities":

[

    "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:1421787800:inso",
    "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:1421786393:cgeek",
    "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:1421790376:moul",
    "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:1421787461:galuel"

],
"joiners":
[

    "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787800:inso",
    "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421786393:cgeek",
    "BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421790376:moul",
    "37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787461:galuel"

],
"actives": [ ],
"leavers": [ ],
"excluded": [ ],
"certifications":

    [
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
    "transactions": [ ],
    "raw": "Version: 1\nType: Block\nCurrency: meta_brouzouf\nNonce: 10144\nNumber: 0\nPoWMin: 3\nTime: 1421838980\nMedianTime: 1421838980\nIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nParameters: 0.1:86400:100:604800:2629800:3:3:2629800:3:11:600:20:144:0.67\nMembersCount: 4\nIdentities:\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:Ot3zIp/nsHT3zgJy+2YcXPL6vaM5WFsD+F8w3qnJoBRuBG6lv761zoaExp2iyUnm8fDAyKPpMxRK2kf437QSCw==:1421787800:inso\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:GZKLgaxJKL+GqxVLePMt8OVLJ6qTLrib5Mr/j2gjiNRY2k485YLB2OlzhBzZVnD3xLs0xi69JUfmLnM54j3aCA==:1421786393:cgeek\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:th576H89dfymkG7/sH+DAIzjlmIqNEW6zY3ONrGeAml+k3f1ver399kYnEgG5YCaKXnnVM7P0oJHah80BV3mDw==:1421790376:moul\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:XRmbTYFkPeGVEU2mJzzN4h1oVNDsZ4yyNZlDAfBm9CWhBsZ82QqX9GPHye2hBxxiu4Nz1BHgQiME6B4JcAC8BA==:1421787461:galuel\nJoiners:\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:ccJm3F44eLMhQtnQY/7+14SWCDqVTL3Miw65hBVpV+YiUSUknIGhBNN0C0Cf+Pf0/pa1tjucW8Us3z5IklFSDg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787800:inso\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1lFIiaR0QX0jibr5zQpXVGzBvMGqcsTRlmHiwGz5HOAZT8PTdVUb5q6YGZ6qAUZjdMjPmhLaiMIpYc47wUnzBA==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421786393:cgeek\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:ctyAhpTRrAAOhFJukWI8RBr//nqYYdQibVzjOfaCdcWLb3TNFKrNBBothNsq/YrYHr7gKrpoftucf/oxLF8zAg==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421790376:moul\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:uoiGaC5b7kWqtqdPxwatPk9QajZHCNT9rf8/8ud9Rli24z/igcOf0Zr4A6RTAIKWUq9foW39VqJe+Y9R3rhACw==:0:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709:1421787461:galuel\nActives:\nLeavers:\nExcluded:\nCertifications:\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:3wmCVW8AbVxRFm2PuLXD9UTCIg93MhUblZJvlYrDldSV4xuA7mZCd8TV4vb/6Bkc0FMQgBdHtpXrQ7dpo20uBA==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:7UMQsUjLvuiZKIzOH5rrZDdDi5rXUo69EuQulY1Zm42xpRx/Gt5CkoTcJ/Mu83oElQbcZZTz/lVJ6IS0jzMiCQ==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:0:twWSY9etI82FLEHzhdqIoHsC9ehWCA7DCPiGxDLCWGPO4TG77hwtn3RcC68qoKHCib577JCp+fcKyp2vyI6FDA==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:7K5MHkO8ibf5SchmPkRrmsg9owEZZ23uEMJJSQYG7L3PUmAKmmV/0VSjivxXH8gJGQBGsXQoK79x1jsYnj2nAg==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:Jua4FcEJFptSE5OoG1/Mgzx4e9jgGnYu7t8g1sqqPujI9hRhLFNXbQXedPS1q1OD5vWivA045gKOq/gnj8opDg==\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:0:R/DV4/wYjvBG09QSOGtnxd3bfPFhVjEE5Uy3BsBMVUvjLsgxjf8NgLhYVozcHTRWS43ArxlXKfS5m3+KIPhhAQ==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:4hP+ahJK021akL4UxB6c5QLaGJXa9eapd3nfdFQe+Xy87f/XLhj8BCa22XbbOlyGdaZRT3AYzbCL2UD5tI8mCw==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:sZTQJr0d/xQnxrIIdSePUJpSTOa8v6IYGXMF2fVDZxQU8vwfzPm2dUKTaF0nU6E9wOYszzkBHaXL85nir+WtCQ==\n37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:BMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:0:hDuBkoFhWhR/FgOU1+9SbQGBMIr47xqUzw1ZMERaPQo4aWm0WFbZurG4lvuJZzTyG6RF/gSw4VPvYZFPxWmADg==\n8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:79ZVrBehElVZh82fJdR18IJx06GkEVZTbwdHH4zb0S6VaGwdtLh1rvomm4ukBvUc8r/suTweG/SScsJairXNAg==\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:e/ai9E4G5CFB9Qi329e0ffYpZMgxj8mM4rviqIr2+UESA0UG86OuAAyHO11hYeyolZRiU8I7WdtNE98B1uZuBg==\nBMAVuMDcGhYAV4wA27DL1VXX2ZARZGJYaMwpf7DJFMYH:37qBxM4hLV2jfyYo2bNzAjkeLngLr2r7G2HpdpKieVxw:0:q4PCneYkcPH8AHEqEvqTtYQWslhlYO2B87aReuOl1uPczn5Q3VkZFAsU48ZTYryeyWp2nxdQojdFYhlAUNchAw==\nTransactions:\n"

}"""

bma_peering = b"""{

    "version": 1,
    "currency": "meta_brouzouf",
    "endpoints":

    [
        "BASIC_MERKLED_API  localhost 0.0.0.0 8000"
    ],
    "status": "UP",
    "block": "0-DA39A3EE5E6B4B0D3255BFEF95601890AFD80709",
    "signature": "boZBmPJUcL11O+RxiL7nEoxueUObOr7SqZVLFJFbxEeMe9mKgfOmBIZ5ch09s1n0cIx6BFlMbVl0yiy23h31Cw==",
    "raw": "Version: 1\nType: Peer\nCurrency: meta_brouzouf\nPublicKey: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nBlock: 0-DA39A3EE5E6B4B0D3255BFEF95601890AFD80709\nEndpoints:\nBASIC_MERKLED_API  localhost 0.0.0.0 8000\n",
    "pubkey": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"

}"""


def get_mock():
    # Assume a running server
    # Initialise the mock client and clear all responses
    mock = HTTPMock('127.0.0.1', 50000)

    mock.when('GET /network/peering')\
        .reply(body=bma_peering,
                times=FOREVER,
                headers={'Content-Type': 'application/json'})

    # For GET requests to /hello reply with a body of 'Hello'
    mock.when('GET /blockchain/Block/0')\
        .reply(body=b"Block not found",
               status=404,
               times=FOREVER,
                headers={'Content-Type': 'application/json'})

    # For GET requests to /hello reply with a body of 'Hello'
    mock.when('GET /blockchain/current')\
        .reply(body=b"Block not found",
               status=404,
               times=FOREVER,
                headers={'Content-Type': 'application/json'})
    return mock
