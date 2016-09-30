from PyQt5.QtCore import QObject, QCoreApplication, QT_TRANSLATE_NOOP, QLocale, QDateTime
from .base_referential import BaseReferential


class UDDToPast(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('UDDToPast', 'Past UUD')
    _REF_STR_ = QT_TRANSLATE_NOOP('UDDToPast', "{0} {1}UUD({2}) {3}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('UDDToPast', "UUD({0}) {1}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('UDDToPast',
                                      """R = Q / UD(t)
                                        <br >
                                        <table>
                                        <tr><td>R</td><td>Dividend per day in percent</td></tr>
                                        <tr><td>t</td><td>Last UD time</td></tr>
                                        <tr><td>Q</td><td>Quantitative value</td></tr>
                                        <tr><td>UD</td><td>Universal Dividend</td></tr>
                                        <tr><td>t</td><td>Time when the value appeared</td></tr>
                                        <tr><td>DT</td><td>Delay between two UD in days</td></tr>
                                        </table>>"""
                                      )
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('UDDToPast',
                                          """Universal Dividend per Day displayed in percent, using UD at the Time
                                          when the value appeared.
                                          The purpose is to have a default unit that is easy to use and understand.
                                          100 UDD equal the Universal Dividend created per day.
                                          Relative referential
                                          Relative value R is calculated by dividing the quantitative value Q by the
                                          """.replace('\n', '<br >'))

    def __init__(self, amount, community, app, block_number=None):
        super().__init__(amount, community, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('UDDToPast', UDDToPast._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("UDDToPast", UDDToPast._UNITS_STR_).format('t', self.community.short_currency)
    @property
    def formula(self):
        return QCoreApplication.translate('UDDToPast', UDDToPast._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("UDDToPast", UDDToPast._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    async def value(self):
        """
        Return relative value of amount

        value = (Q * 100) / R
        Q = Quantitative value
        R = UD(t) of one day
        t = last UD block time

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        dividend = await self.community.dividend()
        params = await self.community.parameters()
        if dividend > 0:
            return (self.amount * 100) / (float(dividend) / (params['dt'] / 86400))
        else:
            return self.amount

    async def differential(self):
        """
        Return relative value of amount

        value = (Q * 100) / R
        Q = Quantitative value
        R = UD(t) of one day
        t = UD block time of when the value was created

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        dividend = await self.community.dividend(self._block_number)
        params = await self.community.parameters()
        if dividend > 0:
            return (self.amount * 100) / (float(dividend) / (params['dt'] / 86400))
        else:
            return self.amount

    async def localized(self, units=False, international_system=False):
        from . import Relative
        value = await self.value()
        block = await self.community.get_block()
        prefix = ""
        if international_system:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("UDDToPast", UDDToPast._REF_STR_) \
                .format(localized_value,
                        prefix,
                        QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(block['medianTime']).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        from . import Relative
        value = await self.differential()
        block = await self.community.get_block(self._block_number)
        prefix = ""
        if international_system and value != 0:
            localized_value, prefix = Relative.to_si(value, self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("UDDToPast", UDDToPast._REF_STR_)\
                .format(localized_value,
                    prefix,
                    QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(block['medianTime']).date(),
                        QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.community.short_currency if units else "")
        else:
            return localized_value
