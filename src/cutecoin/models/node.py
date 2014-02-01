'''
Created on 1 févr. 2014

@author: inso
'''

class Node(object):
    '''
    classdocs
    '''


    def __init__(self, server, port, auth):
        '''
        Constructor
        '''
        self.server = server
        self.port = port
        self.auth = auth
