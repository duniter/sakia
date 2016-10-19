

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
        pass

    @property
    def units(self):
        pass

    @property
    def diff_units(self):
        pass

    async def value(self):
        pass

    async def differential(self):
        pass

    @staticmethod
    def to_si(value, digits):
        pass

    async def localized(self, units=False, international_system=False):
        pass

    async def diff_localized(self, units=False, international_system=False):
        pass
