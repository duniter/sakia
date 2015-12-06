from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from .relative import Relative
import asyncio

class RelativeZSum:
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', 'Relat Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "{0} R0 {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "R0 {0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('RelativeZSum', RelativeZSum._NAME_STR_)

    @classmethod
    def units(cls, currency):
        return QCoreApplication.translate("RelativeZSum", RelativeZSum._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(cls, currency):
        return RelativeZSum.units(currency)

    async def value(self):
        """
        Return relative value of amount minus the average value

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        ud_block = await self.community.get_ud_block()
        if ud_block and ud_block['membersCount'] > 0:
            monetary_mass = await self.community.monetary_mass()
            dividend = await self.community.dividend()
            median = monetary_mass / ud_block['membersCount']
            relative_value = self.amount / float(dividend)
            relative_median = median / dividend
        else:
            relative_value = self.amount
            relative_median = 0
        return relative_value - relative_median

    async def differential(self):
        return Relative(self.amount, self.community, self.app).value()

    async def localized(self, units=False, international_system=False):
        value = await self.value()

        localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units:
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_)\
                .format(localized_value,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        value = await self.differential()

        localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units:
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_)\
                .format(localized_value, self.community.short_currency if units else "")
        else:
            return localized_value
