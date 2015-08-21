from PyQt5.QtCore import QObject, QCoreApplication, QT_TRANSLATE_NOOP, QLocale


class Relative(QObject):
    _NAME_STR_ = QT_TRANSLATE_NOOP('Relative', 'UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('Relative',  "{0} UD {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Relative',  "UD {0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Relative', Relative._NAME_STR_)

    @classmethod
    def units(self, currency):
        return QCoreApplication.translate("Relative", Relative._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(self, currency):
        return self.units(currency)

    def compute(self):
        """
        Return relaive value of amount
    type
        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: float
        """
        if self.community.dividend > 0:
            return self.amount / float(self.community.dividend)
        else:
            return 0

    def differential(self):
        return self.compute()

    def localized(self, pretty_print=False):
        value = self.compute()
        if pretty_print:
            pass
        else:
            strvalue = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])
            return QCoreApplication.translate("Relative", Relative._REF_STR_).format(strvalue,
                                                                                        self.community.currency)

    def diff_localized(self, pretty_print=False):
        value = self.differential()
        if pretty_print:
            pass
        else:
            strvalue = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])
            return QCoreApplication.translate("Relative", Relative._REF_STR_).format(strvalue,
                                                                                        self.community.currency)
