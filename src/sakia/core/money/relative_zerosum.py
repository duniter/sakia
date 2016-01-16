from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from .relative import Relative
import asyncio


class RelativeZSum:
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', 'Relat Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "{0} R0 {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "R0 {0}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('RelativeZSum',
                                      """R0 = (R / UD(t)) - (( M(t-1) / N(t) ) / UD(t))
                                        <br >
                                        <table>
                                        <tr><td>R0</td><td>Relative value at zero sum</td></tr>
                                        <tr><td>R</td><td>Relative value</td></tr>
                                        <tr><td>M</td><td>Monetary mass</td></tr>
                                        <tr><td>N</td><td>Members count</td></tr>
                                        <tr><td>t</td><td>Last UD time</td></tr>
                                        <tr><td>t-1</td><td>Penultimate UD time</td></tr>
                                        </table>""")
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('RelativeZSum',
                                          """Relative at zero sum is used to display the difference between
                                            the relative value and the average relative value.
                                            If it is positive, the value is above the average value, and if it is negative,
                                            the value is under the average value.
                                           """.replace('\n', '<br >'))

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
    def formula(cls):
        return QCoreApplication.translate('RelativeZSum', RelativeZSum._FORMULA_STR_)

    @classmethod
    def description(cls):
        return QCoreApplication.translate("RelativeZSum", RelativeZSum._DESCRIPTION_STR_)

    @classmethod
    def diff_units(cls, currency):
        return Relative.units(currency)

    @asyncio.coroutine
    def value(self):
        """
        Return relative value of amount minus the average value

        t = last UD block
        t-1 = penultimate UD block
        M = Monetary mass
        N = Members count

        zsum value = (value / UD(t)) - (( M(t-1) / N(t) ) / UD(t))

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        ud_block = yield from self.community.get_ud_block()
        ud_block_minus_1 = yield from self.community.get_ud_block(1)
        if ud_block_minus_1 and ud_block['membersCount'] > 0:
            median = ud_block_minus_1['monetaryMass'] / ud_block['membersCount']
            relative_value = self.amount / float(ud_block['dividend'])
            relative_median = median / ud_block['dividend']
        else:
            relative_value = self.amount
            relative_median = 0
        return relative_value - relative_median

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
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_) \
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
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_) \
                .format(localized_value, self.community.short_currency if units else "")
        else:
            return localized_value
