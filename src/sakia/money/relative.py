from .base_referential import BaseReferential
from .currency import shortened
from ..data.processors import BlockchainProcessor

from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale


class Relative(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('Relative', 'UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('Relative', "{0} {1}{2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Relative', "UD")
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
        return cls(amount, currency, app, block_number)
        
    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Relative', Relative._NAME_STR_)

    @property
    def units(self):
            return QCoreApplication.translate("Relative", Relative._UNITS_STR_)

    @property
    def formula(self):
            return QCoreApplication.translate('Relative', Relative._FORMULA_STR_)

    @property
    def description(self):
            return QCoreApplication.translate("Relative", Relative._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return self.units

    @staticmethod
    def base_str(base):
        return ""

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

    def localized(self, units=False, show_base=False):
        value = self.value()
        localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units:
            return QCoreApplication.translate("Relative", Relative._REF_STR_) \
                .format(localized_value, "",
                        (self.units if units else ""))
        else:
            return localized_value

    def diff_localized(self, units=False, show_base=False):
        value = self.differential()
        localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units:
            return QCoreApplication.translate("Relative", Relative._REF_STR_) \
                .format(localized_value, "",
                        (self.diff_units if units else ""))
        else:
            return localized_value
