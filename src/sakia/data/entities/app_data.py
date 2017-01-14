import attr


@attr.s()
class AppData:
    profiles = attr.ib(default=attr.Factory(list))
    default = attr.ib(convert=str, default="Default Profile")
