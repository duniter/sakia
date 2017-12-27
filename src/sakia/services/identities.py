from PyQt5.QtCore import QObject
import asyncio
from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID, block_uid
from sakia.errors import NoPeerAvailable
from sakia.data.entities import Certification
import logging


class IdentitiesService(QObject):
    """
    Identities service is managing identities data received
    to update data locally
    """
    def __init__(self, currency, connections_processor, identities_processor, certs_processor,
                 blockchain_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor for given currency
        :param sakia.data.processors.CertificationsProcessor certs_processor: the certifications processor for given currency
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor for given currency
        :param sakia.data.processors.ConnectionsProcessor connections_processor: the connections processor
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._connections_processor = connections_processor
        self._identities_processor = identities_processor
        self._certs_processor = certs_processor
        self._blockchain_processor = blockchain_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    def certification_expired(self, cert_time):
        """
        Return True if the certificaton time is too old

        :param int cert_time: the timestamp of the certification
        """
        parameters = self._blockchain_processor.parameters(self.currency)
        blockchain_time = self._blockchain_processor.time(self.currency)
        return blockchain_time - cert_time > parameters.sig_validity

    def certification_writable(self, cert_time):
        """
        Return True if the certificaton time is too old

        :param int cert_time: the timestamp of the certification
        """
        parameters = self._blockchain_processor.parameters(self.currency)
        blockchain_time = self._blockchain_processor.time(self.currency)
        return blockchain_time - cert_time < parameters.sig_window * parameters.avg_gen_time

    def expiration_date(self, identity):
        """
        Get the expiration date of the identity
        :param sakia.data.entities.Identity identity:
        :return: the expiration timestamp
        :rtype: int
        """
        validity = self._blockchain_processor.parameters(self.currency).ms_validity
        if identity.membership_timestamp:
            return identity.membership_timestamp + validity
        else:
            return 0

    def _get_connections_identities(self):
        """
        :rtype: List of sakia.data.entities.Identity
        """
        connections = self._connections_processor.connections_with_uids(self.currency)
        identities = []
        for c in connections:
            identities.append(self._identities_processor.get_identity(self.currency, c.pubkey))
        return identities

    def is_identity_of_connection(self, identity):
        return identity.pubkey in self._connections_processor.pubkeys()

    async def load_memberships(self, identity):
        """
        Request the identity data and save it to written identities
        It does nothing if the identity is already written and updated with blockchain lookups
        :param sakia.data.entities.Identity identity: the identity
        """
        try:
            search = await self._bma_connector.get(self.currency, bma.blockchain.memberships,
                                                   req_args={'search': identity.pubkey})
            blockstamp = BlockUID.empty()
            membership_data = None

            for ms in search['memberships']:
                if ms['blockNumber'] > blockstamp.number:
                    blockstamp = BlockUID(ms["blockNumber"], ms['blockHash'])
                    membership_data = ms
            if membership_data:
                identity.membership_timestamp = await self._blockchain_processor.timestamp(self.currency,
                                                                                           blockstamp.number)
                identity.membership_buid = blockstamp
                identity.membership_type = ms["membership"]
                identity.membership_written_on = ms["written"]
                identity = await self.load_requirements(identity)
            # We save connections pubkeys
            identity.written = True
            if self.is_identity_of_connection(identity):
                self._identities_processor.insert_or_update_identity(identity)
        except errors.DuniterError as e:
            logging.debug(str(e))
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                identity.written = False
                if self.is_identity_of_connection(identity):
                    self._identities_processor.insert_or_update_identity(identity)
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return identity

    async def load_certs_in_lookup(self, identity, certifiers, certified):
        """
        :param sakia.data.entities.Identity identity: the identity
        :param list[sakia.data.entities.Certification] certifiers: the list of certifiers got in /wot/certifiers-of
        :param list[sakia.data.entities.Certification] certified: the list of certified got in /wot/certified-by
        """
        try:
            lookup_data = await self._bma_connector.get(self.currency, bma.wot.lookup,
                                                 {'search': identity.pubkey})
            for result in lookup_data['results']:
                if result["pubkey"] == identity.pubkey:
                    for uid_data in result['uids']:
                        if not identity.uid or uid_data["uid"] == identity.uid:
                            if not identity.blockstamp or identity.blockstamp == block_uid(uid_data["meta"]["timestamp"]):
                                for other_data in uid_data["others"]:
                                    cert = Certification(currency=self.currency,
                                                         certified=identity.pubkey,
                                                         certifier=other_data["pubkey"],
                                                         block=other_data["meta"]["block_number"],
                                                         timestamp=0,
                                                         signature=other_data['signature'])
                                    if cert not in certifiers:
                                        cert.timestamp = await self._blockchain_processor.timestamp(self.currency,
                                                                                                    cert.block)
                                        certifiers.append(cert)
                                        # We save connections pubkeys
                                        if self.is_identity_of_connection(identity):
                                            self._certs_processor.insert_or_update_certification(cert)
                for signed_data in result["signed"]:
                    cert = Certification(currency=self.currency,
                                         certified=signed_data["pubkey"],
                                         certifier=identity.pubkey,
                                         block=signed_data["cert_time"]["block"],
                                         timestamp=0,
                                         signature=signed_data['signature'])
                    if cert not in certified:
                        certified.append(cert)
                        # We save connections pubkeys
                        if self.is_identity_of_connection(identity):
                            cert.timestamp = await self._blockchain_processor.timestamp(self.currency,
                                                                                        cert.block)
                            self._certs_processor.insert_or_update_certification(cert)
        except errors.DuniterError as e:
            logging.debug("Certified by error : {0}".format(str(e)))
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return certifiers, certified

    async def load_certifiers_of(self, identity):
        """
        Request the identity data and save it to written certifications
        It does nothing if the identity is already written and updated with blockchain lookups
        :param sakia.data.entities.Identity identity: the identity
        """
        certifications = []
        try:
            data = await self._bma_connector.get(self.currency, bma.wot.certifiers_of,
                                                 {'search': identity.pubkey})
            for certifier_data in data['certifications']:
                cert = Certification(currency=self.currency,
                                     certified=data["pubkey"],
                                     certifier=certifier_data["pubkey"],
                                     block=certifier_data["cert_time"]["block"],
                                     timestamp=certifier_data["cert_time"]["medianTime"],
                                     signature=certifier_data['signature'])
                if certifier_data['written']:
                    cert.written_on = certifier_data['written']['number']
                certifications.append(cert)
                # We save connections pubkeys
                if identity.pubkey in self._connections_processor.pubkeys():
                    self._certs_processor.insert_or_update_certification(cert)

            identity.written = True
            if self.is_identity_of_connection(identity):
                self._identities_processor.insert_or_update_identity(identity)
        except errors.DuniterError as e:
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                identity.written = False
                if identity.pubkey in self._connections_processor.pubkeys():
                    self._identities_processor.insert_or_update_identity(identity)
                logging.debug("Certified by error : {0}".format(str(e)))
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return certifications

    async def load_certified_by(self, identity):
        """
        Request the identity data and save it to written certifications
        It does nothing if the identity is already written and updated with blockchain lookups
        :param sakia.data.entities.Identity identity: the identity
        """
        certifications = []
        try:
            data = await self._bma_connector.get(self.currency, bma.wot.certified_by, {'search': identity.pubkey})
            for certified_data in data['certifications']:
                cert = Certification(currency=self.currency,
                                     certifier=data["pubkey"],
                                     certified=certified_data["pubkey"],
                                     block=certified_data["cert_time"]["block"],
                                     timestamp=certified_data["cert_time"]["medianTime"],
                                     signature=certified_data['signature'])
                if certified_data['written']:
                    cert.written_on = certified_data['written']['number']
                certifications.append(cert)
                # We save connections pubkeys
                if identity.pubkey in self._connections_processor.pubkeys():
                    self._certs_processor.insert_or_update_certification(cert)

            identity.written = True
            if self.is_identity_of_connection(identity):
                self._identities_processor.insert_or_update_identity(identity)
        except errors.DuniterError as e:
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                logging.debug("Certified by error : {0}".format(str(e)))
                identity.written = False
                if identity.pubkey in self._connections_processor.pubkeys():
                    self._identities_processor.insert_or_update_identity(identity)
        except NoPeerAvailable as e:
            logging.debug(str(e))
        return certifications

    async def initialize_certifications(self, identity, log_stream=None, progress=None):
        """
        Initialize certifications to and from a given identity
        :param sakia.data.entities.Identity identity:
        :param function log_stream: Logger function
        :param function progress: Progress function for progress bar
        """
        if log_stream:
            log_stream("Requesting certifiers of data")
        certifiers = await self.load_certifiers_of(identity)

        if log_stream:
            log_stream("Requesting certified by data")
        certified = await self.load_certified_by(identity)

        if log_stream:
            log_stream("Requesting lookup data")
        certifiers, certified = await self.load_certs_in_lookup(identity, certifiers, certified)

        if log_stream:
            log_stream("Requesting identities of certifications")
        identities = []
        i = 0
        nb_certs = len(certified + certifiers)
        for cert in certifiers:
            if log_stream:
                log_stream("Requesting identity... {0}/{1}".format(i, nb_certs))
            i += 1
            if progress:
                progress(1/nb_certs)
            certifier = self.get_identity(cert.certifier)
            if not certifier:
                certifier = await self.find_from_pubkey(cert.certifier)
                certifier = await self.load_requirements(certifier)
                identities.append(certifier)

        for cert in certified:
            if log_stream:
                log_stream("Requesting identity... {0}/{1}".format(i, nb_certs))
            i += 1
            if progress:
                progress(1/nb_certs)
            certified = self.get_identity(cert.certified)
            if not certified:
                certified = await self.find_from_pubkey(cert.certified)
                certified = await self.load_requirements(certified)
                identities.append(certified)
        if log_stream:
            log_stream("Commiting identities...")
        for idty in identities:
            self._identities_processor.insert_or_update_identity(idty)

    def _parse_median_time(self, block):
        """
        Parse revoked pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of identities updated
        """
        identities = []
        connections_identities = self._get_connections_identities()
        parameters = self._blockchain_processor.parameters(block.currency)
        for idty in connections_identities:
            if idty.member and idty.membership_timestamp + parameters.ms_validity < block.mediantime:
                identities.append(idty)
        return identities

    def _parse_revocations(self, block):
        """
        Parse revoked pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of identities updated
        """
        revoked = []
        connections_identities = self._get_connections_identities()
        for idty in connections_identities:
            for rev in block.revoked:
                if rev.pubkey == idty.pubkey:
                    idty.revoked_on = block.number
                    revoked.append(idty)
        return revoked

    def _parse_identities(self, block):
        """
        Parse revoked pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of identities updated
        """
        identities = []
        connections_identities = self._get_connections_identities()
        for idty in connections_identities:
            for idty_doc in block.identities:
                if idty_doc.pubkey == idty.pubkey:
                    idty.written = True
                    identities.append(idty)
        return identities

    def _parse_memberships(self, block):
        """
        Parse memberships pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of pubkeys requiring a refresh of requirements
        """
        need_refresh = []
        connections_identities = self._get_connections_identities()
        for ms in block.joiners + block.actives:
            # we update every written identities known locally
            for identity in connections_identities:
                if ms.issuer == identity:
                    identity.membership_written_on = block.number
                    identity.membership_type = "IN"
                    identity.membership_buid = ms.membership_ts
                    identity.written = True
                    self._identities_processor.insert_or_update_identity(identity)
                    # If the identity was not member
                    # it can become one
                    if not identity.member:
                        need_refresh.append(identity)

        for ms in block.leavers:
            # we update every written identities known locally
            for identity in connections_identities:
                identity.membership_written_on = block.number
                identity.membership_type = "OUT"
                identity.membership_buid = ms.membership_ts
                identity.written = True
                self._identities_processor.insert_or_update_identity(identity)
                # If the identity was a member
                # it can stop to be one
                if identity.member:
                    need_refresh.append(identity)

        return need_refresh

    async def _parse_certifications(self, block):
        """
        Parse certified pubkeys found in a block and refresh local data
        This method only creates certifications if one of both identities is
        locally known as written.
        This method returns the identities needing to be refreshed. These can only be
        the identities which we already known as written before parsing this certification.
        :param duniterpy.documents.Block block:
        :return:
        """
        connections_identities = self._get_connections_identities()
        need_refresh = []
        parameters = self._blockchain_processor.parameters(self.currency)
        current_ts = self._blockchain_processor.time(self.currency)
        for identity in connections_identities:
            if self._certs_processor.drop_expired(identity, sig_validity=parameters.sig_validity,
                                                  sig_window=parameters.sig_window,
                                                  current_ts=current_ts):
                need_refresh.append(identity)

            for cert in block.certifications:
            # if we have are a target or a source of the certification
                if cert.pubkey_from == identity.pubkey or cert.pubkey_to in identity.pubkey:
                    identity.written = True
                    timestamp = await self._blockchain_processor.timestamp(self.currency, cert.timestamp.number)
                    self._certs_processor.create_or_update_certification(self.currency, cert, timestamp, block.blockUID)
                    need_refresh.append(identity)

        return need_refresh

    async def load_requirements(self, identity):
        """
        Refresh a given identity information
        :param sakia.data.entities.Identity identity:
        :return:
        """
        try:
            requirements = await self._bma_connector.get(self.currency, bma.wot.requirements,
                                                         req_args={'search': identity.pubkey})
            for identity_data in requirements['identities']:
                if not identity.uid or identity.uid == identity_data["uid"]:
                    if not identity.blockstamp or identity.blockstamp == block_uid(identity_data["meta"]["timestamp"]):
                        identity.uid = identity_data["uid"]
                        identity.blockstamp = block_uid(identity_data["meta"]["timestamp"])
                        identity.timestamp = await self._blockchain_processor.timestamp(self.currency, identity.blockstamp.number)
                        identity.outdistanced = identity_data["outdistanced"]
                        identity.written = identity_data["wasMember"]
                        identity.sentry = identity_data["isSentry"]
                        identity.member = identity_data["membershipExpiresIn"] > 0
                        median_time = self._blockchain_processor.time(self.currency)
                        expiration_time = self._blockchain_processor.parameters(self.currency).ms_validity
                        identity.membership_timestamp = median_time - (expiration_time - identity_data["membershipExpiresIn"])
                        # We save connections pubkeys
                        if self._identities_processor.get_identity(self.currency, identity.pubkey, identity.uid):
                            self._identities_processor.insert_or_update_identity(identity)
        except errors.DuniterError as e:
            if e.ucode == errors.NO_MEMBER_MATCHING_PUB_OR_UID:
                pass
            else:
                self._logger.debug(str(e))
        except NoPeerAvailable as e:
            self._logger.debug(str(e))
        return identity

    async def parse_block(self, block):
        """
        Parse a block to refresh local data
        :param block:
        :return:
        """
        self._parse_revocations(block)
        need_refresh = []
        need_refresh += self._parse_identities(block)
        need_refresh += self._parse_memberships(block)
        need_refresh += await self._parse_certifications(block)
        need_refresh += self._parse_median_time(block)
        return set(need_refresh)

    async def handle_new_blocks(self, blocks):
        """
        Handle new block received and refresh local data
        :param duniterpy.documents.Block block: the received block
        """
        need_refresh = []
        for block in blocks:
            need_refresh += await self.parse_block(block)
        refresh_futures = []
        # for every identity for which we need a refresh, we gather
        # requirements requests
        for identity in set(need_refresh):
            refresh_futures.append(self.load_requirements(identity))
        await asyncio.gather(*refresh_futures)
        return need_refresh

    async def lookup(self, text):
        """
        Lookup for a given text in the network and in local db
        :param str text: text contained in identity data
        :rtype: list[sakia.data.entities.Identity]
        :return: the list of identities found
        """
        return await self._identities_processor.lookup(self.currency, text)

    def insert_or_update_identity(self, identity):
        return self._identities_processor.insert_or_update_identity(identity)

    def get_identity(self, pubkey, uid=""):
        return self._identities_processor.get_identity(self.currency, pubkey, uid)

    async def find_from_pubkey(self, pubkey):
        return await self._identities_processor.find_from_pubkey(self.currency, pubkey)

    def ms_time_remaining(self, identity):
        return self.expiration_date(identity) - self._blockchain_processor.time(identity.currency)

    def certifications_received(self, pubkey):
        """
        Get the list of certifications received by a given identity
        :param str pubkey: the pubkey
        :rtype: list[Certification]
        """
        return self._certs_processor.certifications_received(self.currency, pubkey)

    def certifications_sent(self, pubkey):
        """
        Get the list of certifications received by a given identity
        :param str pubkey: the pubkey
        :rtype: list[Certification]
        """
        return self._certs_processor.certifications_sent(self.currency, pubkey)
