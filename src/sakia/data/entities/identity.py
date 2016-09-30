import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Identity:
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    uid = attr.ib(convert=str, default="")
    blockstamp = attr.ib(convert=block_uid, default=BlockUID.empty())
    signature = attr.ib(convert=str, default="", cmp=False, hash=False)
    timestamp = attr.ib(convert=int, default=0, cmp=False, hash=False)
    written_on = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    revoked_on = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    member = attr.ib(validator=attr.validators.instance_of(bool), default=False, cmp=False, hash=False)
    membership_buid = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    membership_timestamp = attr.ib(convert=int, default=0, cmp=False, hash=False)
    membership_type = attr.ib(convert=str, default='', validator=lambda s, a, t: t in ('', 'IN', 'OUT'), cmp=False, hash=False)
    membership_written_on = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
