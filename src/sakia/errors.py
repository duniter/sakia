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


class NotEnoughChangeError(Error):

    """
    Exception raised when trying to send money but user
    is missing change
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
