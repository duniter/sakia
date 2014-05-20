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
    Exception raised when looking for a person in a community
    who isnt present in key list
    '''

    def __init__(self, class_type, value, community):
        '''
        Constructor
        '''
        super(
            PersonNotFoundError,
            self) .__init(
            "Person looked by " +
            class_type +
            " in " +
            type +
            " not found ")


class CommunityNotFoundError(Error):

    '''
    Exception raised when looking for community in an account list
    '''

    def __init__(self, keyid, amendmentid):
        '''
        Constructor
        '''
        super(CommunityNotFoundError, self) \
            .__init("Community with amendment " + amendmentid
                    + " not found in account " + keyid)


class KeyAlreadyUsed(Error):

    '''
    Exception raised trying to add an account using
    a key already used for another account.
    '''

    def __init__(self, new_account, keyid, found_account):
        '''
        Constructor
        '''
        super(
            KeyAlreadyUsed,
            self) .__init__(
            "Cannot add account " +
            new_account.name +
            " : "
            " the pgpKey " +
            keyid +
            " is already used by " +
            found_account.name)
