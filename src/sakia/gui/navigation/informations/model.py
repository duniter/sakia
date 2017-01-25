import logging
import math

from PyQt5.QtCore import QLocale, QDateTime, pyqtSignal, QObject
from sakia.errors import NoPeerAvailable
from sakia.helpers import timestamp_to_dhms
from sakia.money.currency import shortened
from sakia.money import Referentials
from duniterpy.api import errors


class InformationsModel(QObject):
    """
    An component
    """
    localized_data_changed = pyqtSignal(dict)

    def __init__(self, parent, app, connection, blockchain_service, identities_service, sources_service):
        """
        Constructor of an component

        :param sakia.gui.informations.controller.InformationsController parent: the controller
        :param sakia.app.Application app: the app
        :param sakia.data.entities.Connection connection: the user connection of this node
        :param sakia.services.BlockchainService blockchain_service: the service watching the blockchain state
        :param sakia.services.IdentitiesService identities_service: the service watching the identities state
        :param sakia.services.SourcesService sources_service: the service watching the sources states
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self.sources_service = sources_service
        self._logger = logging.getLogger('sakia')

    def get_localized_data(self):
        localized_data = {}
        #  try to request money parameters
        try:
            params = self.blockchain_service.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return None

        localized_data['growth'] = params.c
        localized_data['days_per_dividend'] = QLocale().toString(params.dt / 86400, 'f', 2)

        last_ud, last_ud_base = self.blockchain_service.last_ud()
        members_count = self.blockchain_service.last_members_count()
        previous_ud, previous_ud_base = self.blockchain_service.previous_ud()
        previous_ud_time = self.blockchain_service.previous_ud_time()
        previous_monetary_mass = self.blockchain_service.previous_monetary_mass()
        previous_members_count = self.blockchain_service.previous_members_count()

        localized_data['units'] = self.app.current_ref.instance(0,
                                                                self.connection.currency,
                                                                self.app, None).units
        localized_data['diff_units'] = self.app.current_ref.instance(0,
                                                                     self.connection.currency,
                                                                     self.app, None).diff_units

        if last_ud:
            # display float values
            localized_data['ud'] = self.app.current_ref.instance(last_ud * math.pow(10, last_ud_base),
                                              self.connection.currency,
                                              self.app).diff_localized(False, True)

            localized_data['members_count'] = self.blockchain_service.current_members_count()

            computed_dividend = self.blockchain_service.computed_dividend()
            # display float values
            localized_data['ud_plus_1'] = self.app.current_ref.instance(computed_dividend,
                                              self.connection.currency, self.app).diff_localized(False, True)

            localized_data['mass'] = self.app.current_ref.instance(self.blockchain_service.current_mass(),
                                              self.connection.currency, self.app).localized(False, True)

            localized_data['ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(self.blockchain_service.last_ud_time()),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )
            localized_data['next_ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(self.blockchain_service.last_ud_time() + params.dt),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )

            if previous_ud:
                mass_minus_1_per_member = (float(0) if previous_ud == 0 or previous_members_count == 0 else
                                           previous_monetary_mass / previous_members_count)
                localized_data['mass_minus_1_per_member'] = self.app.current_ref.instance(mass_minus_1_per_member,
                                                  self.connection.currency, self.app) \
                                                  .localized(False, True)
                localized_data['mass_minus_1'] = self.app.current_ref.instance(previous_monetary_mass,
                                                  self.connection.currency, self.app) \
                                                  .localized(False, True)
                # avoid divide by zero !
                if members_count == 0 or previous_members_count == 0:
                    localized_data['actual_growth'] = float(0)
                else:
                    localized_data['actual_growth'] = (last_ud * math.pow(10, last_ud_base)) / (
                    previous_monetary_mass / members_count)

                localized_data['ud_median_time_minus_1'] = QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(previous_ud_time),
                    QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                )
        return localized_data

    def get_identity_data(self):
        amount = self.sources_service.amount(self.connection.pubkey)
        localized_amount = self.app.current_ref.instance(amount,
                                                         self.connection.currency,
                                                         self.app).localized(False, True)
        mstime_remaining_text = self.tr("Expired or never published")
        outdistanced_text = self.tr("Outdistanced")
        is_member = False
        nb_certs = 0

        if self.connection.uid:
            try:
                identity = self.identities_service.get_identity(self.connection.pubkey, self.connection.uid)
                mstime_remaining = self.identities_service.ms_time_remaining(identity)
                is_member = identity.member
                nb_certs = len(self.identities_service.certifications_received(identity.pubkey))
                if not identity.outdistanced:
                    outdistanced_text = self.tr("In WoT range")

                if mstime_remaining > 0:
                    days, hours, minutes, seconds = timestamp_to_dhms(mstime_remaining)
                    mstime_remaining_text = self.tr("Expires in ")
                    if days > 0:
                        mstime_remaining_text += "{days} days".format(days=days)
                    else:
                        mstime_remaining_text += "{hours} hours and {min} min.".format(hours=hours,
                                                                                       min=minutes)
            except errors.DuniterError as e:
                if e.ucode == errors.NO_MEMBER_MATCHING_PUB_OR_UID:
                    pass
                else:
                    self._logger.error(str(e))

        return {
            'amount': localized_amount,
            'outdistanced': outdistanced_text,
            'nb_certs': nb_certs,
            'mstime': mstime_remaining_text,
            'membership_state': is_member
        }

    def parameters(self):
        """
        Get community parameters
        """
        return self.blockchain_service.parameters()

    def referentials(self):
        """
        Get referentials
        :return: The list of instances of all referentials
        :rtype: list
        """
        refs_instances = []
        for ref_class in Referentials:
             refs_instances.append(ref_class(0, self.connection.currency, self.app, None))
        return refs_instances

    def short_currency(self):
        """
        Get community currency
        :return: the community in short currency format
        """
        return shortened(self.connection.currency)