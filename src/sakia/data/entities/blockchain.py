import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Blockchain:
    current_buid = attr.ib(convert=block_uid, default=BlockUID.empty())
    nb_members = attr.ib(convert=int, default=0, cmp=False)
    current_mass = attr.ib(convert=int, default=0, cmp=False)
    median_time = attr.ib(convert=int, default=0, cmp=False)
    last_ud = attr.ib(convert=int, default=0, cmp=False)
    last_ud_base = attr.ib(convert=int, default=0, cmp=False)
    previous_mass = attr.ib(convert=int, default=0, cmp=False)
    currency = attr.ib(convert=str, default="", cmp=False)
