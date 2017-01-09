from .base_referential import BaseReferential
from .currency import shortened
from ..data.processors import BlockchainProcessor

from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale


class Relative(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('Relative', 'UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('Relative', "{0} {1}UD{2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Relative', "UD {0}")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('Relative',
                                      """R = Q / UD(t)
                                        <br >
                                        <table>
                                        <tr><td>R</td><td>Relative value</td></tr>
                                        <tr><td>Q</td><td>Quantitative value</td></tr>
                                        <tr><td>UD</td><td>Universal Dividend</td></tr>
                                        <tr><td>t</td><td>Last UD time</td></tr>
                                        </table>"""
                                      )
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('Relative',
                                          """Relative referential of the money.
                                          Relative value R is calculated by dividing the quantitative value Q by the last
                                           Universal Dividend UD.
                                          This referential is the most practical one to display prices and accounts.
                                          No money creation or destruction is apparent here and every account tend to
                                           the average.
                                          """.replace('\n', '<br >'))

    def __init__(self, amount, currency, app, block_number=None):
        super().__init__(amount, currency, app, block_number)
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)

    @classmethod
    def instance(cls, amount, currency, app, block_number=None):
        """

        :param int amount:
        :param str currency:
        :param sakia.app.Application app:
        :param int block_number:
        :return:
        """
        if app.parameters.forgetfulness:
            return cls(amount, currency, app, block_number)
        else:
            return RelativeToPast(amount, currency, app, block_number)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Relative', Relative._NAME_STR_)

    @property
    def units(self):
            return QCoreApplication.translate("Relative", Relative._UNITS_STR_).format(shortened(self.currency))

    @property
    def formula(self):
            return QCoreApplication.translate('Relative', Relative._FORMULA_STR_)

    @property
    def description(self):
            return QCoreApplication.translate("Relative", Relative._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    def value(self):
        """
        Return relative value of amount

        value = amount / UD(t)

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        dividend, base = self._blockchain_processor.last_ud(self.currency)
        if dividend > 0:
            return self.amount / (float(dividend * (10**base)))
        else:
            return self.amount

    def differential(self):
        return self.value()

    @staticmethod
    def to_si(value, digits):
        unicodes = {
            '0': ord('\u2070'),
            '1': ord('\u00B9'),
            '2': ord('\u00B2'),
            '3': ord('\u00B3'),
        }
        for n in range(4, 10):
            unicodes[str(n)] = ord('\u2070') + n

        if value < 0:
            value = -value
            multiplier = -1
        else:
            multiplier = 1
        scientific_value = value
        exponent = 0

        while scientific_value < 0.01:
            exponent += 3
            scientific_value *= 1000

        if exponent > 1:
            localized_value = QLocale().toString(float(scientific_value * multiplier), 'f', digits)
            power_of_10 = "x10⁻" + "".join([chr(unicodes[e]) for e in str(exponent)])
        else:
            localized_value = QLocale().toString(float(value * multiplier), 'f', digits)
            power_of_10 = ""

        return localized_value, power_of_10

    def localized(self, units=False, international_system=False):
        value = self.value()
        prefix = ""
        if international_system:
            localized_value, prefix = Relative.to_si(value, self.app.parameters.digits_after_comma)
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units or international_system:
            return QCoreApplication.translate("Relative", Relative._REF_STR_) \
                .format(localized_value,
                        prefix + " " if prefix else "",
                        (" " + shortened(self.currency)) if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = self.differential()
        prefix = ""
        if international_system and value != 0:
            localized_value, prefix = Relative.to_si(value, self.app.parameters.digits_after_comma)
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units or international_system:
            return QCoreApplication.translate("Relative", Relative._REF_STR_) \
                .format(localized_value,
                        prefix + " " if prefix else "",
                        (" " + shortened(self.currency)) if units else "")
        else:
            return localized_value
