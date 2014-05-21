'''
Created on 21 mai 2014

@author: inso
'''

import math

class Algorithm(object):
    '''
    classdocs
    '''
    def __init__(self, parameters):
        '''
        Constructor
        '''
        self.parameters = parameters

    def coin_value(self, amendement, coin_number):
        pass


class Base2Draft(Algorithm):

    def __init__(self, parameters):
        super.__init__(parameters)

    def coin_value(self, amendment, coin_number):
        coin_base = amendment['CoinBase']
        coins_list = amendment['CoinsList']
        i = 0
        while coin_number > coins_list[i]:
            coin_number -= coins_list[i]
            i += 1
        return math.pow(2, coin_base + i)
