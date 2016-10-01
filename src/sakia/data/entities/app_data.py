import attr


@attr.s()
class AppData:
    profiles = attr.ib(default=attr.Factory(list))
