from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
from . import relative


class RelativeZSum:
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', 'Relat Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "{0} R0 {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "R0 {0}")

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
    def diff_units(cls, currency):
        return RelativeZSum.units(currency)

    def value(self):
        """
        Return relative value of amount minus the average value

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: float
        """
        ud_block = self.community.get_ud_block()
        if ud_block and ud_block['membersCount'] > 0:
            median = self.community.monetary_mass / ud_block['membersCount']
            relative_value = self.amount / float(self.community.dividend)
            relative_median = median / self.community.dividend
        else:
            relative_median = 0
        return relative_value - relative_median

    def differential(self):
        return relative.compute(self.amount, self.community)

    def localized(self, pretty_print=False):
        value = self.compute(self.amount, self.community)
        return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_).format(value, self.community)

    def diff_localized(self, pretty_print=False):
        return relative.amount_to_str(self.amount, self.community, pretty_print)