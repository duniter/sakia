from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QObject, QLocale
import asyncio

class Quantitative():
    _NAME_STR_ = QT_TRANSLATE_NOOP('Quantitative', 'Units')
    _REF_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0} {1}{2}")
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

    @asyncio.coroutine
    def value(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount)

    @asyncio.coroutine
    def differential(self):
        value = yield from self.value()
        return value

    @staticmethod
    def to_si(value, digits):
        prefixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'z', 'y']
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

    @asyncio.coroutine
    def localized(self, units=False, international_system=False):
        value = yield from self.value()
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

    @asyncio.coroutine
    def diff_localized(self, units=False, international_system=False):
        value = yield from self.differential()
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
