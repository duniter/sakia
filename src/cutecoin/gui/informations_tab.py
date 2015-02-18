"""
Created on 31 janv. 2015

@author: vit
"""

import logging
import datetime
from PyQt5.QtWidgets import QWidget
from ..gen_resources.informations_tab_uic import Ui_InformationsTabWidget


class InformationsTabWidget(QWidget, Ui_InformationsTabWidget):
    """
    classdocs
    """

    def __init__(self, account, community):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.community = community
        self.account = account

        self.refresh()

    def refresh(self):
        #  try to request money parameters
        try:
            params = self.community.get_parameters()
        except Exception as e:
            logging.debug('community get_parameters error : ' + str(e))
            return False

        #  try to request money variables from last ud block
        try:
            block = self.community.get_ud_block()
        except Exception as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False
        try:
            block_t_minus_1 = self.community.get_ud_block(1)
        except Exception as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False

        # set infos in label
        self.label_general.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:.2f}</b></div></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:.2f}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:.2f}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:2.2%} / {:} days</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format(
                self.get_referential_diff_value(block['dividend']),
                'Universal Dividend UD(t) in',
                self.get_referential_name(),
                self.get_referential_value(block['monetaryMass']),
                'Monetary Mass M(t) in',
                self.get_referential_name(),
                block['membersCount'],
                'Members N(t)',
                self.get_referential_value(block['monetaryMass'] / block['membersCount']),
                'Monetary Mass per member M(t)/N(t) in',
                self.get_referential_name(),
                block['dividend'] / (block_t_minus_1['monetaryMass'] / block['membersCount']),
                params['dt'] / 86400,
                'Actual growth c = UD(t)/[M(t-1)/N(t)]',
                datetime.datetime.fromtimestamp(block['medianTime'] + params['dt']).strftime("%d/%m/%Y %I:%M"),
                'Next UD date and time (t+1)'
            )
        )

        # set infos in label
        self.label_money.setText(
            """
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
            """.format(
                params['c'],
                params['dt'] / 86400,
                'Fundamental growth (c)',
                params['ud0'],
                'Initial Universal Dividend UD(0) in',
                self.community.short_currency,
                params['dt'] / 86400,
                'Time period (dt) in days (86400 seconds) between two UD',
                params['medianTimeBlocks'],
                'Number of blocks used for calculating median time',
                params['avgGenTime'],
                'The average time in seconds for writing 1 block (wished time)',
                params['dtDiffEval'],
                'The number of blocks required to evaluate again PoWMin value',
                params['blocksRot'],
                'The number of previous blocks to check for personalized difficulty',
                params['percentRot'],
                'The percent of previous issuers to reach for personalized difficulty'
            )
        )

        # set infos in label
        self.label_rules.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format(
                '{:2.0%} / {:} days'.format(params['c'], params['dt'] / 86400),
                'Fundamental growth (c) / Delta time (dt)',
                'UD(t+1) = MAX { UD(t) ; c * M(t) / N(t) }',
                'Universal Dividend (formula)',
                'UD(t+1) = MAX {{ {:.2f} {:} ; {:2.0%} * {:.2f} {:} / {:} }}'.format(
                    self.get_referential_diff_value(block['dividend']),
                    self.get_referential_name(),
                    params['c'],
                    self.get_referential_value(block['monetaryMass']),
                    self.get_referential_name(),
                    block['membersCount']
                ),
                'Universal Dividend (computed)'
            )
        )

        # set infos in label
        self.label_wot.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format(
                params['sigDelay'] / 86400,
                'Minimum delay between 2 identical certifications (in days)',
                params['sigValidity'] / 86400,
                'Maximum age of a valid signature (in days)',
                params['sigQty'],
                'Minimum quantity of signatures to be part of the WoT',
                params['sigWoT'],
                'Minimum quantity of valid made certifications to be part of the WoT for distance rule',
                params['msValidity'] / 86400,
                'Maximum age of a valid membership (in days)',
                params['stepMax'],
                'Maximum distance between each WoT member and a newcomer',
            )
        )

    def get_referential_value(self, value):
        return self.account.units_to_ref(value, self.community)

    def get_referential_diff_value(self, value):
        return self.account.units_to_diff_ref(value, self.community)

    def get_referential_name(self):
        return self.account.ref_name(self.community.short_currency)
