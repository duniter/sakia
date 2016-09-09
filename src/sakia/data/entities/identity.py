import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Identity:
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    uid = attr.ib(convert=str, default="")
    blockstamp = attr.ib(convert=block_uid, default=BlockUID.empty())
    signature = attr.ib(convert=str, default="", cmp=False)
    timestamp = attr.ib(convert=int, default=0, cmp=False)
    written = attr.ib(validator=attr.validators.instance_of(bool), default=False, cmp=False)
    revoked = attr.ib(validator=attr.validators.instance_of(bool), default=False, cmp=False)
    member = attr.ib(validator=attr.validators.instance_of(bool), default=False, cmp=False)
    membership_buid = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False)
    membership_timestamp = attr.ib(convert=int, default=0, cmp=False)
