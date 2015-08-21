from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
from . import Quantitative


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

    def compute(self):
        """
        Return quantitative value of amount minus the average value

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: int
        """
        ud_block = self.community.get_ud_block()
        if ud_block and ud_block['membersCount'] > 0:
            average = self.community.monetary_mass / ud_block['membersCount']
        else:
            average = 0
        return self.amount - average

    def differential(self):
        return Quantitative(self.amount, self.community, self.app).compute()

    def localized(self, pretty_print=False):
        value = self.compute()
        return QCoreApplication.translate("Quantitative", Quantitative._REF_STR_).format(value, self.community.currency)

    def diff_localized(self, pretty_print=False):
        return Quantitative(self.amount, self.community, self.app).amount_to_str(pretty_print)