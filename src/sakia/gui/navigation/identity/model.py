import logging
import math

from PyQt5.QtCore import QLocale, QDateTime, pyqtSignal, QObject, QModelIndex, Qt
from sakia.errors import NoPeerAvailable
from sakia.constants import ROOT_SERVERS
from .table_model import CertifiersTableModel, CertifiersFilterProxyModel
from sakia.data.processors import BlockchainProcessor
from duniterpy.api import errors


class IdentityModel(QObject):
    """
    An component
    """
    localized_data_changed = pyqtSignal(dict)

    def __init__(self, parent, app, connection, blockchain_service, identities_service, sources_service):
        """
        Constructor of an component

        :param sakia.gui.identity.controller.IdentityController parent: the controller
        :param sakia.app.Application app: the app
        :param sakia.data.entities.Connection connection: the user connection of this node
        :param sakia.services.BlockchainService blockchain_service: the service watching the blockchain state
        :param sakia.services.IdentitiesService identities_service: the service watching the identities state
        :param sakia.services.SourcesService sources_service: the service watching the sources states
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.blockchain_processor = BlockchainProcessor.instanciate(app)
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self.sources_service = sources_service
        self.table_model = None
        self.proxy_model = None
        self._logger = logging.getLogger('sakia')

    def init_table_model(self):
        """
        Instanciate the table model of the view
        """
        certifiers_model = CertifiersTableModel(self, self.connection, self.blockchain_service, self.identities_service)
        proxy = CertifiersFilterProxyModel(self.app)
        proxy.setSourceModel(certifiers_model)

        self.table_model = certifiers_model
        self.proxy_model = proxy
        self.table_model.init_certifiers()
        return self.proxy_model

    async def refresh_identity_data(self):
        identity = self.identities_service.get_identity(self.connection.pubkey, self.connection.uid)
        identity = await self.identities_service.load_requirements(identity)

        # update identities in database from the network
        await self.identities_service.initialize_certifications(identity, None, None)

        # update identities from database
        self.table_model.init_certifiers()

    def table_data(self, index):
        if index.isValid() and index.row() < self.table_model.rowCount(QModelIndex()):
            source_index = self.proxy_model.mapToSource(index)
            identity_col = self.table_model.columns_ids.index('identity')
            identity_index = self.table_model.index(source_index.row(), identity_col)
            identity = self.table_model.data(identity_index, Qt.DisplayRole)
            return True, identity
        return False, None

    def get_localized_data(self):
        localized_data = {}
        #  try to request money parameters
        try:
            params = self.blockchain_service.parameters()
        except NoPeerAvailable as e:
            logging.debug('community parameters error : ' + str(e))
            return None

        localized_data['currency'] = ROOT_SERVERS[self.connection.currency]["display"]
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

            ud_median_time = self.blockchain_service.last_ud_time()
            ud_median_time = self.blockchain_processor.adjusted_ts(self.app.currency, ud_median_time)

            localized_data['ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(ud_median_time),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )

            next_ud_median_time = self.blockchain_service.last_ud_time() + params.dt
            next_ud_median_time = self.blockchain_processor.adjusted_ts(self.app.currency, next_ud_median_time)

            localized_data['next_ud_median_time'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(next_ud_median_time),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )

            next_ud_reeval = self.blockchain_service.next_ud_reeval()
            next_ud_reeval = self.blockchain_processor.adjusted_ts(self.app.currency, next_ud_reeval)
            localized_data['next_ud_reeval'] = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(next_ud_reeval),
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

                previous_ud_time = self.blockchain_processor.adjusted_ts(self.app.currency, previous_ud_time)
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
        outdistanced_text = self.tr("Outdistanced")
        is_identity = False
        written = False
        is_member = False
        nb_certs = 0
        mstime_remaining = 0
        identity_expiration = 0
        identity_expired = False
        outdistanced = False
        nb_certs_required = self.blockchain_service.parameters().sig_qty

        if self.connection.uid:
            is_identity = True
            try:
                identity = self.identities_service.get_identity(self.connection.pubkey, self.connection.uid)
                if identity:
                    mstime_remaining = self.identities_service.ms_time_remaining(identity)
                    is_member = identity.member
                    outdistanced = identity.outdistanced
                    written = identity.written
                    if not written:
                        identity_expiration = identity.timestamp + self.parameters().sig_window
                        identity_expired = identity_expiration < self.blockchain_processor.time(self.connection.currency)
                        identity_expiration = self.blockchain_processor.adjusted_ts(self.app.currency,
                                                                                    identity_expiration)
                    nb_certs = len(self.identities_service.certifications_received(identity.pubkey))
                    if not identity.outdistanced:
                        outdistanced_text = self.tr("In WoT range")
            except errors.DuniterError as e:
                if e.ucode == errors.NO_MEMBER_MATCHING_PUB_OR_UID:
                    pass
                else:
                    self._logger.error(str(e))

        return {
            'written': written,
            'idty_expired': identity_expired,
            'idty_expiration': identity_expiration,
            'amount': localized_amount,
            'is_outdistanced': outdistanced,
            'outdistanced': outdistanced_text,
            'nb_certs': nb_certs,
            'nb_certs_required': nb_certs_required,
            'mstime': mstime_remaining,
            'membership_state': is_member,
            'is_identity': is_identity
        }

    def parameters(self):
        """
        Get community parameters
        """
        return self.blockchain_service.parameters()

    def notifications(self):
        return self.app.parameters.notifications

    async def send_join(self, secret_key, password):
        return await self.app.documents_service.send_membership(self.connection, secret_key, password, "IN")
