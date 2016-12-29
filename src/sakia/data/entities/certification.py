import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Certification:
    currency = attr.ib(convert=str)
    certifier = attr.ib(convert=str)
    certified = attr.ib(convert=str)
    block = attr.ib(convert=int)
    timestamp = attr.ib(convert=int)
    signature = attr.ib(convert=str, cmp=False, hash=False)
    written_on = attr.ib(convert=int, default=0, cmp=False, hash=False)
