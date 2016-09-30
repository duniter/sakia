from PyQt5.QtCore import QObject, QCoreApplication, QT_TRANSLATE_NOOP, QLocale, QDateTime
from .base_referential import BaseReferential


class RelativeToPast(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', 'Past UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', "{0} {1}UD({2}) {3}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeToPast', "UD({0}) {1}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('RelativeToPast',
                                      """R = Q / UD(t)
                                        <br >
                                        <table>
                                        <tr><td>R</td><td>Relative value</td></tr>
                                        <tr><td>Q</td><td>Quantitative value</td></tr>
                                        <tr><td>UD</td><td>Universal Dividend</td></tr>
                                        <tr><td>t</td><td>Time when the value appeared</td></tr>
                                        </table>"""
                                      )
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('RelativeToPast',
                                          """Relative referential using UD at the Time when the value appeared.
                                          Relative value R is calculated by dividing the quantitative value Q by the
                                           Universal Dividend UD at the Time when the value appeared.
                                          All past UD created are displayed with a value of 1 UD.
                                          This referential is practical to remember what was the value at the Time.
                                          """.replace('\n', '<br >'))

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
    def formula(self):
        return QCoreApplication.translate('RelativeToPast', RelativeToPast._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("RelativeToPast", RelativeToPast._DESCRIPTION_STR_)

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
        from . import Relative
        value = await self.value()
        block = await self.community.get_ud_block()
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
                            QDateTime.fromTime_t(block['medianTime']).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        self.community.short_currency if units else "")
        else:
            return localized_value

    async def diff_localized(self, units=False, international_system=False):
        from . import Relative
        value = await self.differential()
        block = await self.community.get_ud_block(0, self._block_number)
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
                        QDateTime.fromTime_t(block['medianTime']).date(),
                        QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.community.short_currency if units else "")
        else:
            return localized_value
