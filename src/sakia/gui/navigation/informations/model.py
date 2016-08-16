from sakia.gui.component.model import ComponentModel
from sakia.tools.exceptions import NoPeerAvailable
from PyQt5.QtCore import QLocale, QDateTime, pyqtSignal
from sakia.core.money import Referentials

import logging
import math


class InformationsModel(ComponentModel):
    """
    An component
    """
    localized_data_changed = pyqtSignal(dict)

    def __init__(self, parent, app, account, community):
        """
        Constructor of an component

        :param sakia.gui.informations.controller.InformationsController parent: the controller
        :param sakia.core.Application app: the app
        :param sakia.core.Account account: the account
        :param sakia.core.Community community: the community
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community

    async def get_localized_data(self):
        localized_data = {}
        #  try to request money parameters
        try:
            params = await self.community.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return None

        localized_data['growth'] = params['c']
        localized_data['days_per_dividend'] = params['dt'] / 86400

        try:
            block_ud = await self.community.get_ud_block()
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))

        try:
            block_ud_minus_1 = await self.community.get_ud_block(x=1)
        except NoPeerAvailable as e:
            logging.debug('community get_ud_block error : ' + str(e))

        localized_data['units'] = self.account.current_ref.instance(0, self.community, self.app, None).units
        localized_data['diff_units'] = self.account.current_ref.instance(0, self.community, self.app, None).diff_units

        if block_ud:
            # display float values
            localized_data['ud'] = await self.account.current_ref.instance(block_ud['dividend'] * math.pow(10, block_ud['unitbase']),
                                              self.community,
                                              self.app) \
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            localized_data['members_count'] = block_ud['membersCount']

            computed_dividend = await self.community.computed_dividend()
            # display float values
            localized_data['ud_plus_1'] = await self.account.current_ref.instance(computed_dividend,
                                              self.community, self.app) \
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            localized_data['mass'] = await self.account.current_ref.instance(block_ud['monetaryMass'],
                                              self.community, self.app) \
                .diff_localized(True, self.app.preferences['international_system_of_units'])

            localized_data['ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(block_ud['medianTime']),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )

            localized_data['next_ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(block_ud['medianTime'] + params['dt']),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )

            if block_ud_minus_1:
                mass_minus_1 = (float(0) if block_ud['membersCount'] == 0 else
                                block_ud_minus_1['monetaryMass'] / block_ud['membersCount'])
                localized_data['mass_minus_1_per_member'] = await self.account.current_ref.instance(mass_minus_1,
                                                  self.community, self.app) \
                                                .diff_localized(True, self.app.preferences['international_system_of_units'])
                localized_data['mass_minus_1'] = await self.account.current_ref.instance(block_ud_minus_1['monetaryMass'],
                                                  self.community, self.app) \
                                                    .diff_localized(True, self.app.preferences['international_system_of_units'])
                # avoid divide by zero !
                if block_ud['membersCount'] == 0 or block_ud_minus_1['monetaryMass'] == 0:
                    localized_data['actual_growth'] = float(0)
                else:
                    localized_data['actual_growth'] = (block_ud['dividend'] * math.pow(10, block_ud['unitbase'])) / (
                    block_ud_minus_1['monetaryMass'] / block_ud['membersCount'])

                localized_data['ud_median_time_minus_1'] = QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(block_ud_minus_1['medianTime']),
                    QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                )
        return localized_data

    async def get_identity_data(self):
        amount = await self.app.current_account.amount(self.community)
        localized_amount = await self.app.current_account.current_ref.instance(amount,
                                                                               self.community, self.app).localized(
            units=True,
            international_system=self.app.preferences['international_system_of_units'])
        account_identity = await self.app.current_account.identity(self.community)

        mstime_remaining_text = self.tr("Expired or never published")
        outdistanced_text = self.tr("Outdistanced")

        requirements = await account_identity.requirements(self.community)
        mstime_remaining = 0
        nb_certs = 0
        if requirements:
            mstime_remaining = requirements['membershipExpiresIn']
            nb_certs = len(requirements['certifications'])
            if not requirements['outdistanced']:
                outdistanced_text = self.tr("In WoT range")

        if mstime_remaining > 0:
            days, remainder = divmod(mstime_remaining, 3600 * 24)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            mstime_remaining_text = self.tr("Expires in ")
            if days > 0:
                mstime_remaining_text += "{days} days".format(days=days)
            else:
                mstime_remaining_text += "{hours} hours and {min} min.".format(hours=hours,
                                                                               min=minutes)
        return {
            'amount': localized_amount,
            'outdistanced': outdistanced_text,
            'nb_certs': nb_certs,
            'mstime': mstime_remaining_text,
            'membership_state': mstime_remaining > 0
        }

    async def parameters(self):
        """
        Get community parameters
        """
        #  try to request money parameters
        try:
            params = await self.community.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return None
        return params

    def referentials(self):
        """
        Get referentials
        :return: The list of instances of all referentials
        :rtype: list
        """
        refs_instances = []
        for ref_class in Referentials:
             refs_instances.append(ref_class(0, self.community, self.app, None))
        return refs_instances

    def short_currency(self):
        """
        Get community currency
        :return: the community in short currency format
        """
        return self.community.short_currency