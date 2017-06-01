import attr


@attr.s(hash=True)
class Dividend:
    currency = attr.ib(convert=str, cmp=True, hash=True)
    pubkey = attr.ib(convert=str, cmp=True, hash=True)
    block_number = attr.ib(convert=int, cmp=True, hash=True)
    timestamp = attr.ib(convert=int)
    amount = attr.ib(convert=int, cmp=False, hash=False)
    base = attr.ib(convert=int, cmp=False, hash=False)
