import attr
from sakia.helpers import attrs_tuple_of_str


@attr.s()
class Contact:
    """
    A contact in the network currency
    """
    currency = attr.ib(convert=str)
    name = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    fields = attr.ib(convert=attrs_tuple_of_str, default="")
    contact_id = attr.ib(convert=int, default=-1)
