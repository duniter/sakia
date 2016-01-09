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

    @asyncio.coroutine
    def value(self):
        """
        Return relative value of amount minus the average value

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        current = yield from self.community.get_block()
        if current and current['membersCount'] > 0:
            monetary_mass = yield from self.community.monetary_mass()
            dividend = yield from self.community.dividend()
            average = monetary_mass / current['membersCount']
            rz_value = (self.amount - average) / float(dividend)
        else:
            rz_value = self.amount
        return rz_value

    @asyncio.coroutine
    def differential(self):
        return Relative(self.amount, self.community, self.app).value()

    @asyncio.coroutine
    def localized(self, units=False, international_system=False):
        value = yield from self.value()

        prefix = ""
        if international_system:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units:
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_)\
                .format(localized_value,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = yield from self.differential()

        prefix = ""
        if international_system and value != 0:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units:
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_)\
                .format(localized_value, self.community.short_currency if units else "")
        else:
            return localized_value
