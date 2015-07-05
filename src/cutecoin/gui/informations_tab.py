"""
Created on 31 janv. 2015

@author: vit
"""

import logging
import math
from PyQt5.QtCore import QLocale, QDateTime
from PyQt5.QtWidgets import QWidget
from ..gen_resources.informations_tab_uic import Ui_InformationsTabWidget


class InformationsTabWidget(QWidget, Ui_InformationsTabWidget):
    """
    classdocs
    """

    def __init__(self, app, community):
        """
        Constructor of the InformationsTabWidget

        :param app: cutecoin.core.Application
        :param community: cutecoin.core.Community
        :return:
        """
        super().__init__()
        self.app = app
        self.community = community
        self.community.inner_data_changed.connect(self.refresh)

        self.setupUi(self)
        self.refresh()

    @property
    def account(self):
        return self.app.current_account

    def refresh(self):
        #  try to request money parameters
        try:
            params = self.community.parameters
        except Exception as e:
            logging.debug('community parameters error : ' + str(e))
            return False

        #  try to request money variables from last ud block
        try:
            block_ud = self.community.get_ud_block()
        except Exception as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False
        try:
            block_ud_minus_1 = self.community.get_ud_block(1)
        except Exception as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False

        if block_ud:
            ud = self.get_referential_diff_value(block_ud['dividend'])
            # if referential type is quantitative...
            if self.account.ref_type() == 'q':
                # display int values
                # use the float type of 64bits, to avoid display a 32bit signed integer...
                localized_ud = QLocale().toString(float(ud), 'f', 0)
                # display int values
                localized_ud_plus_1 = QLocale().toString(
                    float(
                        self.get_referential_diff_value(
                            self.community.computed_dividend
                        )
                    ),
                    'f',
                    0
                )
                localized_mass = QLocale().toString(
                    float(self.get_referential_diff_value(block_ud['monetaryMass'])), 'f', 0
                )
                if block_ud_minus_1:
                    localized_mass_minus_1_per_member = QLocale().toString(
                        float(
                            self.get_referential_diff_value(float(0) if block_ud['membersCount'] == 0 else
                                block_ud_minus_1['monetaryMass'] / block_ud['membersCount']
                            )
                        ), 'f', 0
                    )
                    localized_mass_minus_1 = QLocale().toString(
                        float(self.get_referential_diff_value(block_ud_minus_1['monetaryMass'])), 'f', 0
                    )
                else:
                    localized_mass_minus_1_per_member = QLocale().toString(
                        float(0), 'f', 0
                    )
                    localized_mass_minus_1 = QLocale().toString(
                        float(0), 'f', 0
                    )
            else:
                # display float values
                localized_ud = QLocale().toString(ud, 'f', self.app.preferences['digits_after_comma'])
                # display float values
                localized_ud_plus_1 = QLocale().toString(
                    float(
                        self.get_referential_diff_value(
                            self.community.computed_dividend
                        )
                    ),
                    'f',
                    self.app.preferences['digits_after_comma']
                )
                localized_mass = QLocale().toString(
                    float(self.get_referential_diff_value(block_ud['monetaryMass'])), 'f', self.app.preferences['digits_after_comma']
                )
                if block_ud_minus_1:
                    localized_mass_minus_1_per_member = QLocale().toString(
                        self.get_referential_diff_value(float(0) if block_ud['membersCount'] == 0 else
                            block_ud_minus_1['monetaryMass'] / block_ud['membersCount']), 'f', self.app.preferences['digits_after_comma']
                    )
                    localized_mass_minus_1 = QLocale().toString(
                        self.get_referential_diff_value(block_ud_minus_1['monetaryMass']), 'f', self.app.preferences['digits_after_comma']
                    )
                else:
                    localized_mass_minus_1_per_member = QLocale().toString(
                        float(0), 'f', self.app.preferences['digits_after_comma']
                    )
                    localized_mass_minus_1 = QLocale().toString(
                        float(0), 'f', self.app.preferences['digits_after_comma']
                    )

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
                </table>
                """).format(
                    localized_ud,
                    self.tr('Universal Dividend UD(t) in'),
                    self.get_referential_diff_name(),
                    localized_mass_minus_1,
                    self.tr('Monetary Mass M(t-1) in'),
                    self.get_referential_diff_name(),
                    block_ud['membersCount'],
                    self.tr('Members N(t)'),
                    localized_mass_minus_1_per_member,
                    self.tr('Monetary Mass per member M(t-1)/N(t) in'),
                    self.get_referential_diff_name(),
                    float(0) if block_ud_minus_1['membersCount'] == 0 else
                    block_ud['dividend'] / (block_ud_minus_1['monetaryMass'] / block_ud_minus_1['membersCount']),

                    params['dt'] / 86400,
                    self.tr('Actual growth c = UD(t)/[M(t-1)/N(t)]'),
                    QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(block_ud['medianTime']),
                        QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.tr('Last UD date and time (t)'),
                    QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(block_ud['medianTime'] + params['dt']),
                        QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.tr('Next UD date and time (t+1)')
                )
            )
        else:
            self.label_general.setText(self.tr('No Universal Dividend created yet.'))

        if block_ud:
            # set infos in label
            self.label_rules.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.tr('{:2.0%} / {:} days').format(params['c'], params['dt'] / 86400),
                    self.tr('Fundamental growth (c) / Delta time (dt)'),
                    self.tr('UD(t+1) = MAX { UD(t) ; c &#215; M(t) / N(t+1) }'),
                    self.tr('Universal Dividend (formula)'),
                    self.tr('{:} = MAX {{ {:} {:} ; {:2.0%} &#215; {:} {:} / {:} }}').format(
                        localized_ud_plus_1,
                        localized_ud,
                        self.get_referential_diff_name(),
                        params['c'],
                        localized_mass,
                        self.get_referential_diff_name(),
                        block_ud['membersCount']
                    ),
                    self.tr('Universal Dividend (computed)')
                )
            )
        else:
            self.label_rules.setText(self.tr('No Universal Dividend created yet.'))

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
                self.community.short_currency,
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
            </table>
            """).format(
                params['sigDelay'] / 86400,
                self.tr('Minimum delay between 2 identical certifications (in days)'),
                params['sigValidity'] / 86400,
                self.tr('Maximum age of a valid signature (in days)'),
                params['sigQty'],
                self.tr('Minimum quantity of signatures to be part of the WoT'),
                params['sigWoT'],
                self.tr('Minimum quantity of valid made certifications to be part of the WoT for distance rule'),
                params['msValidity'] / 86400,
                self.tr('Maximum age of a valid membership (in days)'),
                params['stepMax'],
                self.tr('Maximum distance between each WoT member and a newcomer'),
            )
        )

    def get_referential_value(self, value):
        return self.account.units_to_ref(value, self.community)

    def get_referential_diff_value(self, value):
        return self.account.units_to_diff_ref(value, self.community)

    def get_referential_name(self):
        return self.account.ref_name(self.community.short_currency)

    def get_referential_diff_name(self):
        return self.account.diff_ref_name(self.community.short_currency)
