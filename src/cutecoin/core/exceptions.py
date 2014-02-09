'''
Created on 9 févr. 2014

@author: inso
'''

class Error(Exception):
    def __init__(self, message):
        '''
        Constructor
        '''
        self.message = "Error : " + message


class NotMemberOfCommunityError(Error):
    '''
    Exception raised for error in the input
    '''


    def __init__(self, account, community):
        '''
        Constructor
        '''
        super(NotMemberOfCommunityError, self).__init__(account + " is not a member of " + community)
