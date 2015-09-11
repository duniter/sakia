from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from . import Quantitative
import asyncio

class QuantitativeZSum:
    _NAME_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', 'Quant Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "{0} Q0 {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "Q0 {0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._NAME_STR_)

    @classmethod
    def units(cls, currency):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(cls, currency):
        return QuantitativeZSum.units(currency)

    @asyncio.coroutine
    def value(self):
        """
        Return quantitative value of amount minus the average value

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: int
        """
        ud_block = yield from self.community.get_ud_block()
        if ud_block and ud_block['membersCount'] > 0:
            monetary_mass = yield from self.community.monetary_mass()
            average = monetary_mass / ud_block['membersCount']
        else:
            average = 0
        return self.amount - average

    @asyncio.coroutine
    def differential(self):
        value = yield from Quantitative(self.amount, self.community, self.app).value()
        return value

    @asyncio.coroutine
    def localized(self, units=False, international_system=False):
        value = yield from self.value()
        if international_system:
            pass
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units:
            return QCoreApplication.translate("QuantitativeZSum",
                                              QuantitativeZSum._REF_STR_) \
                .format(localized_value,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    @asyncio.coroutine
    def diff_localized(self, units=False, international_system=False):
        localized = yield from  Quantitative(self.amount, self.community, self.app).localized(units, international_system)
        return localized