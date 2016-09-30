import attr


@attr.s()
class Connection:
    """
    A connection represents a connection to a currency's network
    It is defined by the currency name, and the key informations
    used to connect to it
    """
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    salt = attr.ib(convert=str)
