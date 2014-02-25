'''
Created on 2 févr. 2014

@author: inso
'''

import re
import math
import logging

class Coin(object):
    '''
    A coin parsing a regex to read its value
    '''
    def __init__(self, issuer, number, base, power, origin):
        self.issuer = issuer
        self.number = number
        self.base = base
        self.power = power
        self.origin = origin

    @classmethod
    def fromId(cls, coin_id):
        # Regex to parse the coin id
        regex = "^([A-Z\d]{40})-(\d+)-(\d)-(\d+)-((A|F|D)-\d+)$"
        m = re.search(regex, coin_id)
        issuer = m.group(1)
        number = int(m.group(2))
        base = int(m.group(3))
        power = int(m.group(4))
        origin = m.group(5)
        return cls(issuer, number, base, power, origin)

    def __eq__(self, other):
        return self.getId() == other.getId()

    def value(self):
        return self.base*math.pow(10, self.power)

    def getId(self):
        return self.issuer + "-" \
            + str(self.number) + "-" \
            + str(self.base) + "-" \
            + str(self.power) + "-" \
            + self.origin
