from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from . import Quantitative
from .base_referential import BaseReferential


class QuantitativeZSum(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', 'Quant Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "{0} {1}Q0 {2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "Q0 {0}")

    def __init__(self, amount, community, app, block_number=None):
        super().__init__(amount, community, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._UNITS_STR_).format(self.community.short_currency)

    @property
    def diff_units(self):
        return self.units

    async def value(self):
        """
        Return quantitative value of amount minus the average value

        t = last UD block
        t-1 = penultimate UD block
        M = Monetary mass
        N = Members count

        zsum value = value - ( M(t-1) / N(t) )

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
