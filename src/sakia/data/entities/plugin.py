import attr


@attr.s(frozen=True)
class Plugin:
    name = attr.ib()
    description = attr.ib()
    version = attr.ib()
    imported = attr.ib()
    module = attr.ib()
    filename = attr.ib()
