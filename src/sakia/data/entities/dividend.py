import attr
from duniterpy.documents import block_uid


@attr.s()
class Dividend:
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    block_number = attr.ib(convert=int)
    timestamp = attr.ib(convert=int)
    amount = attr.ib(convert=int, cmp=False, hash=False)
    base = attr.ib(convert=int, cmp=False, hash=False)
