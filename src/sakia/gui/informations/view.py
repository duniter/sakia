from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QEvent
from .informations_uic import Ui_InformationsWidget


class InformationsView(QWidget, Ui_InformationsWidget):
    """
    The view of navigation panel
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

    def set_general_text_no_dividend(self):
        """
        Set the general text when there is no dividend
        """
        self.label_general.setText(self.tr('No Universal Dividend created yet.'))

    def set_general_text(self, localized_data):
        """
        Fill the general text with given informations
        :return:
        """
        # set infos in label
        self.label_general.setText(
            self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></div></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:2.2%} / {:} days</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                localized_data['ud'],
                self.tr('Universal Dividend UD(t) in'),
                localized_data['diff_units'],
                localized_data['mass_minus_1'],
                self.tr('Monetary Mass M(t-1) in'),
                localized_data['units'],
                localized_data['members_count'],
                self.tr('Members N(t)'),
                localized_data['mass_minus_1_per_member'],
                self.tr('Monetary Mass per member M(t-1)/N(t) in'),
                localized_data['diff_units'],
                localized_data['actual_growth'],
                localized_data['days_per_dividend'],
                self.tr('Actual growth c = UD(t)/[M(t-1)/N(t)]'),
                localized_data['ud_median_time_minus_1'],
                self.tr('Penultimate UD date and time (t-1)'),
                localized_data['ud_median_time'],
                self.tr('Last UD date and time (t)'),
                localized_data['next_ud_median_time'],
                self.tr('Next UD date and time (t+1)')
            )
        )

    def set_rules_text_no_dividend(self):
        """
        Set text when no dividends was generated yet
        """
        self.label_rules.setText(self.tr('No Universal Dividend created yet.'))

    def set_rules_text(self, localized_data):
        """
        Set text in rules
        :param dict localized_data:
        :return:
        """
        # set infos in label
        self.label_rules.setText(
            self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                self.tr('{:2.0%} / {:} days').format(localized_data['growth'], localized_data['days_per_dividend']),
                self.tr('Fundamental growth (c) / Delta time (dt)'),
                self.tr('UD(t+1) = MAX { UD(t) ; c &#215; M(t) / N(t+1) }'),
                self.tr('Universal Dividend (formula)'),
                self.tr('{:} = MAX {{ {:} {:} ; {:2.0%} &#215; {:} {:} / {:} }}').format(
                    localized_data['ud_plus_1'],
                    localized_data['ud'],
                    localized_data['diff_units'],
                    localized_data['growth'],
                    localized_data['mass'],
                    localized_data['diff_units'],
                    localized_data['members_count']
                ),
                self.tr('Universal Dividend (computed)')
            )
        )

    def set_text_referentials(self, referentials):
        """
        Set text from referentials
        :param list referentials: list of referentials
        """
        # set infos in label
        ref_template = """
                <table cellpadding="5">
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                </table>
                """
        templates = []
        for ref in referentials:
            # print(ref_class.__class__.__name__)
            # if ref_class.__class__.__name__ == 'RelativeToPast':
            #     continue
            templates.append(ref_template.format(self.tr('Name'), ref.translated_name(),
                                                 self.tr('Units'), ref.units,
                                                 self.tr('Formula'), ref.formula,
                                                 self.tr('Description'), ref.description
                                                 )
                             )

        self.label_referentials.setText('<hr>'.join(templates))

    def set_money_text(self, params, currency):
        """
        Set text from money parameters
        :param dict params: Parameters of the currency
        :param str currency: The currency
        """

        # set infos in label
        self.label_money.setText(
                self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:2.0%} / {:} days</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:2.0%}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                        params['c'],
                        params['dt'] / 86400,
                        self.tr('Fundamental growth (c)'),
                        params['ud0'],
                        self.tr('Initial Universal Dividend UD(0) in'),
                        currency,
                        params['dt'] / 86400,
                        self.tr('Time period (dt) in days (86400 seconds) between two UD'),
                        params['medianTimeBlocks'],
                        self.tr('Number of blocks used for calculating median time'),
                        params['avgGenTime'],
                        self.tr('The average time in seconds for writing 1 block (wished time)'),
                        params['dtDiffEval'],
                        self.tr('The number of blocks required to evaluate again PoWMin value'),
                        params['blocksRot'],
                        self.tr('The number of previous blocks to check for personalized difficulty'),
                        params['percentRot'],
                        self.tr('The percent of previous issuers to reach for personalized difficulty')
                )
        )

    def set_wot_text(self, params):
        """
        Set wot text from currency parameters
        :param dict parameters:
        :return:
        """

        # set infos in label
        self.label_wot.setText(
                self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                        params['sigPeriod'] / 86400,
                        self.tr('Minimum delay between 2 certifications (in days)'),
                        params['sigValidity'] / 86400,
                        self.tr('Maximum age of a valid signature (in days)'),
                        params['sigQty'],
                        self.tr('Minimum quantity of signatures to be part of the WoT'),
                        params['sigStock'],
                        self.tr('Maximum quantity of active certifications made by member.'),
                        params['sigWindow'],
                        self.tr('Maximum delay a certification can wait before being expired for non-writing.'),
                        params['xpercent'],
                        self.tr('Minimum percent of sentries to reach to match the distance rule'),
                        params['msValidity'] / 86400,
                        self.tr('Maximum age of a valid membership (in days)'),
                        params['stepMax'],
                        self.tr('Maximum distance between each WoT member and a newcomer'),
                )
        )

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super().changeEvent(event)
