"""
Created on 9 févr. 2014

@author: inso
"""


class Error(Exception):

    def __init__(self, message):
        """
        Constructor
        """
        self.message = "Error : " + message

    def __str__(self):
        return self.message


class NotMemberOfCommunityError(Error):

    """
    Exception raised when adding a community the account is not a member of
    """

    def __init__(self, account, community):
        """
        Constructor
        """
        super() \
            .__init__(account + " is not a member of " + community)


class LookupFailureError(Error):

    """
    Exception raised when looking for a person in a community
    who isnt present in key list
    """

    def __init__(self, value, community):
        """
        Constructor
        """
        super() .__init__(
            "Person looked by {0} in {1} not found ".format(value, community))


class MembershipNotFoundError(Error):

    """
    Exception raised when looking for a person in a community
    who isnt present in key list
    """

    def __init__(self, value, community):
        """
        Constructor
        """
        super() .__init__(
            "Membership searched by " +
            value +
            " in " +
            community +
            " not found ")


class AlgorithmNotImplemented(Error):

    """
    Exception raised when a coin uses an algorithm not known
    """

    def __init__(self, algo_name):
        """
        Constructor
        """
        super() \
            .__init__("Algorithm " + algo_name + " not implemented.")


class KeyAlreadyUsed(Error):

    """
    Exception raised trying to add an account using
    a key already used for another account.
    """

    def __init__(self, new_account, keyid, found_account):
        """
        Constructor
        """
        super() .__init__(
"""Cannot add account {0} :
the key {1} is already used by {2}""".format(new_account,
                                             keyid,
                                             found_account)
            )


class NameAlreadyExists(Error):

    """
    Exception raised trying to add an account using
    a key already used for another account.
    """

    def __init__(self, account_name):
        """
        Constructor
        """
        super() .__init__(
            "Cannot add account " +
            account_name +
            " the name already exists")


class BadAccountFile(Error):

    """
    Exception raised trying to add an account using
    a key already used for another account.
    """

    def __init__(self, path):
        """
        Constructor
        """
        super() .__init__(
            "File " + path + " is not an account file")


class NotEnoughMoneyError(Error):

    """
    Exception raised trying to add an account using
    a key already used for another account.
    """

    def __init__(self, available, currency, nb_inputs, requested):
        """
        Constructor
        """
        super() .__init__(
            "Only {0} {1} available in {2} sources, needs {3}"
            .format(available,
                    currency,
                    nb_inputs,
                    requested))


class NoPeerAvailable(Error):
    """
    Exception raised when a community doesn't have any
    peer available.
    """
    def __init__(self, currency, nbpeers):
        """
        Constructor
        """
        super() .__init__(
            "No peer answered in {0} community ({1} peers available)"
            .format(currency, nbpeers))


class InvalidNodeCurrency(Error):
    """
    Exception raised when a node doesn't use the intended currency
    """
    def __init__(self, currency, node_currency):
        """
        Constructor
        """
        super() .__init__(
            "Node is working for {0} currency, but should be {1}"
            .format(node_currency, currency))


class ContactAlreadyExists(Error):
    """
    Exception raised when a community doesn't have any
    peer available.
    """
    def __init__(self, new_contact, already_contact):
        """
        Constructor
        """
        super() .__init__(
            "Cannot add {0}, he/she has the same pubkey as {1} contact"
            .format(new_contact, already_contact))
