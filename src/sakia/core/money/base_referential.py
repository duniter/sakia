from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QObject, QLocale
import asyncio


class BaseReferential:
    """
    Interface to all referentials
    """
    def __init__(self, amount, community, app, block_number=None):
        self.amount = amount
        self.community = community
        self.app = app
        self._block_number = block_number

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
