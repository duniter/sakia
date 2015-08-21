from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QObject, QLocale


class Quantitative(QObject):
    _NAME_STR_ = QT_TRANSLATE_NOOP('Quantitative', 'Units')
    _REF_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0} {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Quantitative', 'UD')

    @classmethod
    def units(cls, currency):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(cls, currency):
        return Quantitative.units(currency)

    def compute(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount)

    def differential(self):
        return self.compute()

    def localized(self, pretty_print=False):
        return QCoreApplication.translate("Quantitative", Quantitative._REF_STR_).format(self.amount, self.currency)

    def diff_localized(self, pretty_print=False):
        strvalue = QLocale().toString(float(self.amount), 'f', 0)
        return QCoreApplication.translate("Quantitative", Quantitative._REF_STR_).format(strvalue, self.currency)
