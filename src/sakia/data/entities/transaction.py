import attr
from duniterpy.documents import block_uid


@attr.s()
class Transaction:
    currency = attr.ib(convert=str, cmp=False)
    sha_hash = attr.ib(convert=str)
    written_on = attr.ib(convert=block_uid, cmp=False)
    blockstamp = attr.ib(convert=block_uid, cmp=False)
    timestamp = attr.ib(convert=int, cmp=False)
    signature = attr.ib(convert=str, cmp=False)
    issuer = attr.ib(convert=str, cmp=False)
    receiver = attr.ib(convert=str, cmp=False)
    amount = attr.ib(convert=int, cmp=False)
    amount_base = attr.ib(convert=int, cmp=False)
    comment = attr.ib(convert=str, cmp=False)
    txid = attr.ib(convert=int, cmp=False)
