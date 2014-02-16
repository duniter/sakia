'''
Created on 2 févr. 2014

@author: inso
'''

import re
import math

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
        regex = "/^([A-Z\d]{40})-(\d+)-(\d)-(\d+)-((A|F|D)-\d+))$/"
        m = re.search(regex, coin_id)
        issuer = m.group(0)
        number = int(m.group(1))
        base = int(m.group(2))
        power = int(m.group(3))
        origin = m.group(4)
        return cls(issuer, number, base, power, origin)

    def value(self):
        return math.pow(self.base, self.power)

    def getId(self):
        return self.issuer + "-" \
            + str(self.number) + "-" \
            + str(self.base) + "-" \
            + str(self.power) + "-" \
            + self.origin
