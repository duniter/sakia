import attr
from duniterpy.documents import block_uid


@attr.s()
class Source:
    identifier = attr.ib(convert=str)
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    type = attr.ib(convert=str, validator=lambda i, a, s: s == 'T' or s == 'D')
    offset = attr.ib(convert=int, cmp=False, hash=False)
    amount = attr.ib(convert=int, cmp=False, hash=False)
    base = attr.ib(convert=int, cmp=False, hash=False)
