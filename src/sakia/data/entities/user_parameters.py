import attr


@attr.s()
class UserParameters:
    """
    The user parameters entity
    """
    profile_name = attr.ib(convert=str, default="Default Profile")
    lang = attr.ib(convert=str, default="en_US")
    referential = attr.ib(convert=int, default=0)
    expert_mode = attr.ib(convert=bool, default=False)
    digits_after_comma = attr.ib(convert=int, default=2)
    maximized = attr.ib(convert=bool, default=False)
    notifications = attr.ib(convert=bool, default=True)
    enable_proxy = attr.ib(convert=bool, default=True)
    proxy_type = attr.ib(convert=int, default=0)
    proxy_address = attr.ib(convert=str, default="")
    proxy_port = attr.ib(convert=int, default=8080)
    international_system_of_units = attr.ib(convert=int, default=False)
    forgetfulness = attr.ib(convert=bool, default=True)
