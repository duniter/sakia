"""
Created on 31 janv. 2015

@author: vit
"""

import logging
import asyncio
import math
from PyQt5.QtCore import QLocale, QDateTime, QEvent
from PyQt5.QtWidgets import QWidget
from ..gen_resources.informations_tab_uic import Ui_InformationsTabWidget
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..tools.exceptions import NoPeerAvailable
from .widgets import Busy

class InformationsTabWidget(QWidget, Ui_InformationsTabWidget):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Constructor of the InformationsTabWidget

        :param app: cutecoin.core.Application
        :param community: cutecoin.core.Community
        :return:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = None
        self.community = None
        self.busy = Busy(self.scrollArea)
        self.busy.hide()

    def change_account(self, account):
        cancel_once_task(self, self.refresh_labels)
        self.account = account

    def change_community(self, community):
        cancel_once_task(self, self.refresh_labels)
        self.community = community
        self.refresh()

    def refresh(self):
        if self.account and self.community:
            self.refresh_labels()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def refresh_labels(self):
        self.busy.show()
        #  try to request money parameters
        try:
            params = yield from self.community.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return False

        #  try to request money variables from last ud block
        try:
            block_ud = yield from self.community.get_ud_block()
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False
        try:
            block_ud_minus_1 = yield from self.community.get_ud_block(1)
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False

        if block_ud:
            # display float values
            localized_ud = yield from self.account.current_ref(block_ud['dividend'], self.community, self.app).diff_localized()

            computed_dividend = yield from self.community.computed_dividend()
            # display float values
            localized_ud_plus_1 = yield from self.account.current_ref(computed_dividend,
                                                    self.community, self.app).diff_localized()

            localized_mass = yield from self.account.current_ref(block_ud['monetaryMass'],
                                                    self.community, self.app).diff_localized()
            if block_ud_minus_1:
                mass_minus_1 = (float(0) if block_ud['membersCount'] == 0 else
                        block_ud_minus_1['monetaryMass'] / block_ud['membersCount'])
                localized_mass_minus_1_per_member = yield from self.account.current_ref(mass_minus_1,
                                                                  self.community, self.app).diff_localized()
                localized_mass_minus_1 = yield from self.account.current_ref(block_ud_minus_1['monetaryMass'],
                                                                  self.community, self.app).diff_localized()

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
                    self.account.current_ref.diff_units(self.community.currency),
                    localized_mass_minus_1,
                    self.tr('Monetary Mass M(t-1) in'),
                    self.account.current_ref.diff_units(self.community.currency),
                    block_ud['membersCount'],
                    self.tr('Members N(t)'),
                    localized_mass_minus_1_per_member,
                    self.tr('Monetary Mass per member M(t-1)/N(t) in'),
                    self.account.current_ref.diff_units(self.community.currency),
                    float(0) if block_ud['membersCount'] == 0 or block_ud_minus_1['monetaryMass'] == 0 else
                    block_ud['dividend'] / (block_ud_minus_1['monetaryMass'] / block_ud['membersCount']),

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
                        self.account.current_ref.diff_units(self.community.currency),
                        params['c'],
                        localized_mass,
                        self.account.current_ref.diff_units(self.community.currency),
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
        self.busy.hide()

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super(InformationsTabWidget, self).changeEvent(event)
