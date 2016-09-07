import attr
from duniterpy.documents import block_uid


@attr.s(slots=True)
class Identity:
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    uid = attr.ib(convert=str)
    blockstamp = attr.ib(convert=block_uid)
    signature = attr.ib(convert=str)
    timestamp = attr.ib(convert=int)
    revoked = attr.ib(validator=attr.validators.instance_of(bool))
    member = attr.ib(validator=attr.validators.instance_of(bool))
    membership_buid = attr.ib(convert=block_uid)
    membership_timestamp = attr.ib(convert=int)
