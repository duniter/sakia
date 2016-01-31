"""
Created on 31 janv. 2015

@author: vit
"""

import logging
import asyncio
from PyQt5.QtCore import QLocale, QDateTime, QEvent
from PyQt5.QtWidgets import QWidget
from ..gen_resources.informations_tab_uic import Ui_InformationsTabWidget
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..tools.exceptions import NoPeerAvailable
from .widgets import Busy
from ..core.money import Referentials


class InformationsTabWidget(QWidget, Ui_InformationsTabWidget):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Constructor of the InformationsTabWidget

        :param sakia.core.app.Application app: Application instance

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
        """

        :param sakia.core.app.Account account: Account instance selected
        """
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
    async def refresh_labels(self):
        self.busy.show()
        #  try to request money parameters
        try:
            params = await self.community.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return False

        #  try to request money variables from last ud block
        try:
            block_ud = await self.community.get_ud_block()
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False
        try:
            block_ud_minus_1 = await self.community.get_ud_block(x=1)
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False

        if block_ud:
            # display float values
            localized_ud = await self.account.current_ref(block_ud['dividend'],
                                                               self.community,
                                                               self.app) \
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            computed_dividend = await self.community.computed_dividend()
            # display float values
            localized_ud_plus_1 = await self.account.current_ref(computed_dividend,
                                                    self.community, self.app)\
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            localized_mass = await self.account.current_ref(block_ud['monetaryMass'],
                                                    self.community, self.app)\
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            if block_ud_minus_1:
                mass_minus_1 = (float(0) if block_ud['membersCount'] == 0 else
                        block_ud_minus_1['monetaryMass'] / block_ud['membersCount'])
                localized_mass_minus_1_per_member = await self.account.current_ref(mass_minus_1,
                                                                  self.community, self.app)\
                    .diff_localized(True, self.app.preferences['international_system_of_units'])
                localized_mass_minus_1 = await self.account.current_ref(block_ud_minus_1['monetaryMass'],
                                                                  self.community, self.app)\
                    .diff_localized(True, self.app.preferences['international_system_of_units'])
                # avoid divide by zero !
                if block_ud['membersCount'] == 0 or block_ud_minus_1['monetaryMass'] == 0:
                    actual_growth = float(0)
                else:
                    actual_growth = block_ud['dividend'] / (block_ud_minus_1['monetaryMass'] / block_ud['membersCount'])
            else:
                localized_mass_minus_1_per_member = QLocale().toString(
                        float(0), 'f', self.app.preferences['digits_after_comma']
                )
                localized_mass_minus_1 = QLocale().toString(
                        float(0), 'f', self.app.preferences['digits_after_comma']
                )
                actual_growth = float(0)

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
                    localized_ud,
                    self.tr('Universal Dividend UD(t) in'),
                    self.account.current_ref(0, self.community, self.app, None).diff_units,
                    localized_mass_minus_1,
                    self.tr('Monetary Mass M(t-1) in'),
                    self.account.current_ref(0, self.community, self.app, None).units,
                    block_ud['membersCount'],
                    self.tr('Members N(t)'),
                    localized_mass_minus_1_per_member,
                    self.tr('Monetary Mass per member M(t-1)/N(t) in'),
                    self.account.current_ref(0, self.community, self.app, None).diff_units,
                    actual_growth,
                    params['dt'] / 86400,
                    self.tr('Actual growth c = UD(t)/[M(t-1)/N(t)]'),
                    QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(block_ud_minus_1['medianTime']),
                        QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                    ),
                    self.tr('Penultimate UD date and time (t-1)'),
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
                        self.account.current_ref(0, self.community, self.app, None).diff_units,
                        params['c'],
                        localized_mass,
                        self.account.current_ref(0, self.community, self.app, None).diff_units,
                        block_ud['membersCount']
                    ),
                    self.tr('Universal Dividend (computed)')
                )
            )
        else:
            self.label_rules.setText(self.tr('No Universal Dividend created yet.'))

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
        for ref_class in Referentials:
            ref = ref_class(0, self.community, self.app, None)
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
                        self.tr(
                            'Minimum quantity of valid made certifications to be part of the WoT for distance rule'),
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
