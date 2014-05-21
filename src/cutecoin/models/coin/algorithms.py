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

    def __call__(self, amendment, coin_number):
        pass


class Base2Draft(Algorithm):

    def __init__(self, parameters):
        super().__init__(parameters)

    def __call__(self, amendment, coin_number):
        coin_base = amendment['coinBase']
        coins_list = amendment['coinList']
        i = 0
        while coin_number > coins_list[i]:
            coin_number -= coins_list[i]
            i += 1
        return math.pow(2, coin_base + i)
