from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QLocale
from .relative import Relative
from .base_referential import BaseReferential
from .currency import shortened
from ..data.processors import BlockchainProcessor


class RelativeZSum(BaseReferential):
    _NAME_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', 'Relat Z-sum')
    _REF_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "{0} {1}{2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('RelativeZSum', "R0 UD")
    _FORMULA_STR_ = QT_TRANSLATE_NOOP('RelativeZSum',
                                      """R0 = (Q / UD(t)) - (( M(t-1) / N(t) ) / UD(t))
                                        <br >
                                        <table>
                                        <tr><td>R0</td><td>Relative value at zero sum</td></tr>
                                        <tr><td>R</td><td>Relative value</td></tr>
                                        <tr><td>M</td><td>Monetary mass</td></tr>
                                        <tr><td>N</td><td>Members count</td></tr>
                                        <tr><td>t</td><td>Last UD time</td></tr>
                                        <tr><td>t-1</td><td>Penultimate UD time</td></tr>
                                        </table>""")
    _DESCRIPTION_STR_ = QT_TRANSLATE_NOOP('RelativeZSum',
                                          """Relative at zero sum is used to display the difference between
                                            the relative value and the average relative value.
                                            If it is positive, the value is above the average value, and if it is negative,
                                            the value is under the average value.
                                           """.replace('\n', '<br >'))

    def __init__(self, amount, currency, app, block_number=None):
        super().__init__(amount, currency, app, block_number)
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('RelativeZSum', RelativeZSum._NAME_STR_)

    @property
    def units(self):
        return QCoreApplication.translate("RelativeZSum", RelativeZSum._UNITS_STR_)

    @property
    def formula(self):
        return QCoreApplication.translate('RelativeZSum', RelativeZSum._FORMULA_STR_)

    @property
    def description(self):
        return QCoreApplication.translate("RelativeZSum", RelativeZSum._DESCRIPTION_STR_)

    @property
    def diff_units(self):
        return QCoreApplication.translate("Relative", Relative._UNITS_STR_)

    @staticmethod
    def base_str(base):
        return Relative.base_str(base)

    def value(self):
        """
        Return relative value of amount minus the average value

        t = last UD block
        t-1 = penultimate UD block
        M = Monetary mass
        N = Members count

        zsum value = (value / UD(t)) - (( M(t-1) / N(t) ) / UD(t))

        :param int amount:   Value
        :param sakia.core.community.Community community: Community instance
        :return: float
        """
        dividend, base = self._blockchain_processor.previous_ud(self.currency)
        previous_monetary_mass = self._blockchain_processor.previous_monetary_mass(self.currency)
        members_count = self._blockchain_processor.current_members_count(self.currency)
        if previous_monetary_mass and members_count > 0:
            median = previous_monetary_mass / members_count
            relative_value = self.amount / float(dividend * 10**base)
            relative_median = median / float(dividend * 10**base)
        else:
            relative_value = self.amount
            relative_median = 0
        return relative_value - relative_median

    def differential(self):
        return Relative(self.amount, self.currency, self.app).value()

    def localized(self, units=False, show_base=False):
        value = self.value()

        localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units:
            return QCoreApplication.translate("RelativeZSum", RelativeZSum._REF_STR_)\
                .format(localized_value, "",
                        self.units if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, show_base=False):
        value = self.differential()

        localized_value = QLocale().toString(float(value), 'f', self.app.parameters.digits_after_comma)

        if units:
            return QCoreApplication.translate("Relative", Relative._REF_STR_)\
                .format(localized_value, "",
                        (self.diff_units if units else ""))
        else:
            return localized_value
