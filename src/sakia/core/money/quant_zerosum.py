from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from . import Quantitative
import asyncio


class QuantitativeZSum:
    _NAME_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', 'Quant Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "{0} Q0 {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "Q0 {0}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum',
                                      """Z0 = Q - ( M(t-1) / N(t) )
                                        <br >
                                        <table>
                                        <tr><td>Z0</td><td>Quantitative value at zero sum</td></tr>
                                        <tr><td>Q</td><td>Quantitative value</td></tr>
                                        <tr><td>M</td><td>Monetary mass</td></tr>
                                        <tr><td>N</td><td>Members count</td></tr>
                                        <tr><td>t</td><td>Last UD time</td></tr>
                                        <tr><td>t-1</td><td>Penultimate UD time</td></tr>
                                        </table>"""
                                      )
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum',
                                          """Quantitative at zero sum is used to display the difference between
                                            the quantitative value and the average quantitative value.
                                            If it is positive, the value is above the average value, and if it is negative,
                                            the value is under the average value.
                                           """.replace('\n', '<br >'))

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
    def formula(cls):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._FORMULA_STR_)

    @classmethod
    def description(cls):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._DESCRIPTION_STR_)

    @classmethod
    def diff_units(cls, currency):
        return Quantitative.units(currency)

    @asyncio.coroutine
    def value(self):
        """
        Return quantitative value of amount minus the average value

        Z0 = Q - ( M(t-1) / N(t) )

        Z0 = Quantitative value at zero sum
        Q = Quantitative value
        t = last UD block time
        t-1 = penultimate UD block time
        M = Monetary mass
        N = Members count

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: int
        """
        ud_block = yield from self.community.get_ud_block()
        ud_block_minus_1 = yield from self.community.get_ud_block(1)
        if ud_block_minus_1 and ud_block['membersCount'] > 0:
            average = ud_block_minus_1['monetaryMass'] / ud_block['membersCount']
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

        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, self.app.preferences['digits_after_comma'])
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
        localized = yield from Quantitative(self.amount, self.community, self.app).localized(units,
                                                                                             international_system)
        return localized
