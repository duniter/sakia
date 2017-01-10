from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from .base_referential import BaseReferential
from .currency import shortened
from ..data.processors import BlockchainProcessor


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

    def __init__(self, amount, currency, app, block_number=None):
        super().__init__(amount, currency, app, block_number)
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Quantitative', Quantitative._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format(shortened(self.currency))

    @property
    def formula(self):
        return QCoreApplication.translate('Quantitative', Quantitative._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("Quantitative", Quantitative._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    def value(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount) / 100

    def differential(self):
        return self.value()

    @staticmethod
    def to_si(value, digits):
        unicodes = {
            '0': ord('\u2070'),
            '1': ord('\u00B9'),
            '2': ord('\u00B2'),
            '3': ord('\u00B3'),
        }
        for n in range(4, 10):
            unicodes[str(n)] = ord('\u2070') + n

        if value < 0:
            value = -value
            multiplier = -1
        else:
            multiplier = 1

        scientific_value = value
        exponent = 0

        while scientific_value > 1000 and int(scientific_value) * 10**exponent == value:
            exponent += 3
            scientific_value /= 1000

        if exponent > 1:
            localized_value = QLocale().toString(float(scientific_value * multiplier), 'f', digits)
            power_of_10 = "x10" + "".join([chr(unicodes[e]) for e in str(exponent)])
        else:
            localized_value = QLocale().toString(float(value * multiplier), 'f', 2)
            power_of_10 = ""

        return localized_value, power_of_10

    def localized(self, units=False, international_system=False):
        value = self.value()
        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, 2)
        else:
            localized_value = QLocale().toString(float(value), 'f', 2)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        (" " if prefix and units else "") + (shortened(self.currency) if units else ""))
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = self.differential()
        prefix = ""
        if international_system:
            localized_value, prefix = Quantitative.to_si(value, 2)
        else:
            localized_value = QLocale().toString(float(value), 'f', 2)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        (" " if prefix and units else "") + (shortened(self.currency) if units else ""))
        else:
            return localized_value
