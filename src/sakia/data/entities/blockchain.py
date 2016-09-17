import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Blockchain:
    # block number and hash
    current_buid = attr.ib(convert=block_uid, default=BlockUID.empty())
    # Number of members
    nb_members = attr.ib(convert=int, default=0, cmp=False)
    # Current monetary mass in units
    current_mass = attr.ib(convert=int, default=0, cmp=False)
    # Median time in seconds
    median_time = attr.ib(convert=int, default=0, cmp=False)
    # Last UD amount in units (multiply by 10^base)
    last_ud = attr.ib(convert=int, default=0, cmp=False)
    # Last UD base
    last_ud_base = attr.ib(convert=int, default=0, cmp=False)
    # Previous monetary mass in units
    previous_mass = attr.ib(convert=int, default=0, cmp=False)
    # Currency name
    currency = attr.ib(convert=str, default="", cmp=False)
