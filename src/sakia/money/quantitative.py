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
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format("units")

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
    def base_str(base):
        unicodes = {
            '0': ord('\u2070'),
            '1': ord('\u00B9'),
            '2': ord('\u00B2'),
            '3': ord('\u00B3'),
        }
        for n in range(4, 10):
            unicodes[str(n)] = ord('\u2070') + n

        if base > 0:
            return ".10" + "".join([chr(unicodes[e]) for e in str(base)])
        else:
            return ""

    @staticmethod
    def to_si(value, base):
        if value < 0:
            value = -value
            multiplier = -1
        else:
            multiplier = 1

        scientific_value = value
        scientific_value /= 10**base

        if base > 0:
            localized_value = QLocale().toString(float(scientific_value * multiplier), 'f', 2)
        else:
            localized_value = QLocale().toString(float(value * multiplier), 'f', 2)

        return localized_value

    def localized(self, units=False, show_base=False):
        value = self.value()
        dividend, base = self._blockchain_processor.last_ud(self.currency)
        localized_value = Quantitative.to_si(value, base)
        prefix = Quantitative.base_str(base)

        if units or show_base:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        (" " if prefix and units else "") + (self.units if units else ""))
        else:
            return localized_value

    def diff_localized(self, units=False, show_base=False):
        value = self.differential()
        dividend, base = self._blockchain_processor.last_ud(self.currency)
        localized_value = Quantitative.to_si(value, base)
        prefix = Quantitative.base_str(base)

        if units or show_base:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        (" " if prefix and units else "") + (self.diff_units if units else ""))
        else:
            return localized_value
