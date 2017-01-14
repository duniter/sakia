

class BaseReferential:
    """
    Interface to all referentials
    """
    def __init__(self, amount, currency, app, block_number=None):
        """

        :param int amount:
        :param str currency:
        :param sakia.app.Application app:
        :param int block_number:
        """
        self.amount = amount
        self.app = app
        self.currency = currency
        self._block_number = block_number

    @classmethod
    def instance(cls, amount, currency, app, block_number=None):
        return cls(amount, currency, app, block_number)

    @classmethod
    def translated_name(self):
        raise NotImplementedError()

    @property
    def units(self):
        raise NotImplementedError()

    @property
    def diff_units(self):
        raise NotImplementedError()

    def value(self):
        raise NotImplementedError()

    def differential(self):
        raise NotImplementedError()

    @staticmethod
    def to_si(value, base):
        raise NotImplementedError()

    @staticmethod
    def base_str(base):
        raise NotImplementedError()

    def localized(self, units=False, show_base=False):
        raise NotImplementedError()

    def diff_localized(self, units=False, show_base=False):
        raise NotImplementedError()
