import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s(hash=True)
class Certification:
    currency = attr.ib(convert=str)
    certifier = attr.ib(convert=str)
    certified = attr.ib(convert=str)
    block = attr.ib(convert=int)
    timestamp = attr.ib(convert=int, cmp=False)
    signature = attr.ib(convert=str, cmp=False, hash=False)
    written_on = attr.ib(convert=int, default=-1, cmp=False, hash=False)
