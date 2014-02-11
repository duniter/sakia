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
    Exception raised when adding a community the account is not a member of
    '''
    def __init__(self, account, community):
        '''
        Constructor
        '''
        super(NotMemberOfCommunityError, self) \
            .__init__(account + " is not a member of " + community)

class PersonNotFoundError(Error):
    '''
    Exception raised when looking for a person in a community who isnt present in key list
    '''
    def __init__(self, classType, value, community):
        '''
        Constructor
        '''
        super(PersonNotFoundError, self) \
            .__init("Person looked by " + classType \
                    + " in " + type + " not present in community " + community.name)


class KeyAlreadyUsed(Error):
    '''
    Exception raised trying to add an account using a key already used for another account.
    '''
    def __init__(self, newAccount, keyId, foundAccount):
        '''
        Constructor
        '''
        super(KeyAlreadyUsed, self) \
            .__init("Cannot add account " + newAccount.name + " : " \
                    " the pgpKey " + keyId + " is already used by " + foundAccount.name)


