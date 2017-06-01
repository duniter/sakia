import attr


@attr.s(frozen=True, hash=True)
class Plugin:
    name = attr.ib()
    description = attr.ib(cmp=False, hash=False)
    version = attr.ib(cmp=False, hash=False)
    imported = attr.ib(cmp=False, hash=False)
    module = attr.ib(cmp=False, hash=False)
    filename = attr.ib(cmp=False, hash=False)
