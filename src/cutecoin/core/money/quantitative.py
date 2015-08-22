from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QObject, QLocale


class Quantitative():
    _NAME_STR_ = QT_TRANSLATE_NOOP('Quantitative', 'Units')
    _REF_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0} {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Quantitative', Quantitative._NAME_STR_)

    @classmethod
    def units(cls, currency):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(cls, currency):
        return Quantitative.units(currency)

    def value(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount)

    def differential(self):
        return self.value()

    def localized(self, units=False, international_system=False):
        value = self.value()
        if international_system:
            pass
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = self.differential()
        if international_system:
            pass
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        self.community.short_currency if units else "")
        else:
            return localized_value
