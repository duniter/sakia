import attr
import re
from sakia.helpers import attrs_tuple_of_str


@attr.s(hash=True)
class Contact:
    """
    A contact in the network currency
    """
    re_displayed_text = re.compile("([\w\s\d]+) < ((?![OIl])[1-9A-Za-z]{42,45}) >")

    currency = attr.ib(convert=str)
    name = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    fields = attr.ib(convert=attrs_tuple_of_str, default="")
    contact_id = attr.ib(convert=int, default=-1)

    def displayed_text(self):
        return self.name + " < " + self.pubkey + " > "

