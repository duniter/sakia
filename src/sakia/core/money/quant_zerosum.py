from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from . import Quantitative
from .base_referential import BaseReferential


class QuantitativeZSum(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', 'Quant Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "{0} {1}Q0 {2}")
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

    def __init__(self, amount, community, app, block_number=None):
        super().__init__(amount, community, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._UNITS_STR_).format(self.community.short_currency)

    @property
    def formula(self):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    async def value(self):
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
        ud_block = await self.community.get_ud_block()
        if ud_block and ud_block['membersCount'] > 0:
            monetary_mass = await self.community.monetary_mass()
            average = int(monetary_mass / ud_block['membersCount'])
        else:
            average = 0
        return self.amount - average

    async def differential(self):
        return await Quantitative(self.amount, self.community, self.app).value()

    async def localized(self, units=False, international_system=False):
        value = await self.value()

        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units or international_system:
            return QCoreApplication.translate("QuantitativeZSum",
                                              QuantitativeZSum._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        localized = await Quantitative(self.amount, self.community, self.app).localized(units, international_system)
        return localized
