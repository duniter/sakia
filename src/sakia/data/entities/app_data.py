import attr


@attr.s()
class AppData:
    profiles = attr.ib(factory=list)
