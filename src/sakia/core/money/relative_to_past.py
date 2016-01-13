from PyQt5.QtCore import QObject, QCoreApplication, QT_TRANSLATE_NOOP, QLocale, QDateTime
from .base_referential import BaseReferential
from . import Relative


class RelativeToPast(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', 'Past UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', "{0} {1}UD({2}) {3}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', "UD({0}) {1}")

    def __init__(self, amount, community, app, block_number=None):
        super().__init__(amount, community, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('RelativeToPast', RelativeToPast._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("RelativeToPast", RelativeToPast._UNITS_STR_).format('t',
                                                                                               self.community.short_currency)

    @property
    def diff_units(self):
        return self.units

    async def value(self):
        """
        Return relative to past value of amount
        :return: float
        """
        dividend = await self.community.dividend()
        if dividend > 0:
            return self.amount / float(dividend)
        else:
            return self.amount

    async def differential(self):
        """
        Return relative to past differential value of amount
        :return: float
        """
        dividend = await self.community.dividend(self._block_number)
        if dividend > 0:
            return self.amount / float(dividend)
        else:
            return self.amount

    async def localized(self, units=False, international_system=False):
        value = await self.value()
        block = await self.community.get_block()
        prefix = ""
        if international_system:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("RelativeToPast", RelativeToPast._REF_STR_) \
                .format(localized_value,
                        prefix,
                        QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(block['medianTime']),
                            QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        value = await self.differential()
        block = await self.community.get_block(self._block_number)
        prefix = ""
        if international_system and value != 0:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("RelativeToPast", RelativeToPast._REF_STR_)\
                .format(localized_value,
                    prefix,
                    QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(block['medianTime']),
                        QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.community.short_currency if units else "")
        else:
            return localized_value
