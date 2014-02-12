'''
Created on 11 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Person(object):
    '''
    A person with a name, a fingerprint and an email
    Created by the person.factory
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.name = ""
        self.fingerprint = ""
        self.email = ""