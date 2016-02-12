from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from .base_referential import BaseReferential


class Quantitative(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('Quantitative', 'Units')
    _REF_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0} {1}{2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('Quantitative',
                                      """Q = Q
                                        <br >
                                        <table>
                                        <tr><td>Q</td><td>Quantitative value</td></tr>
                                        </table>
                                      """
                                      )
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('Quantitative', "Base referential of the money. Units values are used here.")

    def __init__(self, amount, community, app, block_number=None):
        super().__init__(amount, community, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Quantitative', Quantitative._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format(self.community.short_currency)

    @property
    def formula(self):
        return QCoreApplication.translate('Quantitative', Quantitative._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("Quantitative", Quantitative._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    async def value(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount)

    async def differential(self):
        return await self.value()

    @staticmethod
    def to_si(value, digits):
        prefixes = ['', 'k', 'M', 'G', 'Tera', 'Peta', 'Exa', 'Zeta', 'Yotta']
        if value < 0:
            value = -value
            multiplier = -1
        else:
            multiplier = 1

        scientific_value = value
        prefix_index = 0
        prefix = ""

        while scientific_value > 1000:
            prefix_index += 1
            scientific_value /= 1000

        if prefix_index < len(prefixes):
            prefix = prefixes[prefix_index]
            localized_value = QLocale().toString(float(scientific_value * multiplier), 'f', digits)
        else:
            localized_value = QLocale().toString(float(value * multiplier), 'f', 0)

        return localized_value, prefix

    async def localized(self, units=False, international_system=False):
        value = await self.value()
        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        value = await self.differential()
        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value
