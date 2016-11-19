import attr
from duniterpy.documents import block_uid


@attr.s()
class Transaction:

    TO_SEND = 0
    AWAITING = 1
    VALIDATING = 2
    VALIDATED = 4
    REFUSED = 8
    DROPPED = 16
    LOCAL = 128

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
    state = attr.ib(convert=int, cmp=False)

    @property
    def local(self):
        return self.state & Transaction.LOCAL == Transaction.LOCAL
