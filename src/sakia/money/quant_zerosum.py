from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from . import Quantitative
from .base_referential import BaseReferential
from .currency import shortened
from ..data.processors import BlockchainProcessor


class QuantitativeZSum(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', 'Quant Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('QuantitativeZSum', "{0}{1}{2}")
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

    def __init__(self, amount, currency, app, block_number=None):
        super().__init__(amount, currency, app, block_number)
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._UNITS_STR_).format("units")

    @property
    def formula(self):
        return QCoreApplication.translate('QuantitativeZSum', QuantitativeZSum._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("QuantitativeZSum", QuantitativeZSum._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format("units")

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
        last_members_count = self._blockchain_processor.last_members_count(self.currency)
        monetary_mass = self._blockchain_processor.current_mass(self.currency)
        if last_members_count != 0:
            average = int(monetary_mass / last_members_count)
        else:
            average = 0
        return (self.amount - average)/100

    @staticmethod
    def base_str(base):
        return Quantitative.base_str(base)

    @staticmethod
    def to_si(value, base):
        return Quantitative.to_si(value, base)

    def differential(self):
        return Quantitative(self.amount, self.currency, self.app).value()

    def localized(self, units=False, show_base=False):
        value = self.value()
        dividend, base = self._blockchain_processor.last_ud(self.currency)

        prefix = ""
        if show_base:
            localized_value = QuantitativeZSum.to_si(value, base)
            prefix = QuantitativeZSum.base_str(base)
        else:
            localized_value = QLocale().toString(float(value), 'f', 2)

        if units or show_base:
            return QCoreApplication.translate("QuantitativeZSum",
                                              QuantitativeZSum._REF_STR_) \
                    .format(localized_value, "",
                            (" " + self.units if units else ""))
        else:
            return localized_value

    def diff_localized(self, units=False, show_base=False):
        localized = Quantitative(self.amount, self.currency, self.app).localized(units, show_base)
        return localized
