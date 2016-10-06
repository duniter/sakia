from PyQt5.QtCore import QObject
import asyncio
from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID
from sakia.errors import NoPeerAvailable
from sakia.data.entities import Certification
import logging


class IdentitiesService(QObject):
    """
    Identities service is managing identities data received
    to update data locally
    """
    def __init__(self, currency, identities_processor, certs_processor, blockchain_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor for given currency
        :param sakia.data.processors.CertificationsProcessor certs_processor: the certifications processor for given currency
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
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

    async def cert_issuance_delay(self, identity):
        """
        Get the remaining time before being able to issue new certification.
        :param sakia.data.entities.Identity identity: the identity
        :return: the remaining time
        """
        if not identity.written_on:
            await self.update_certified_by(identity)
        if len(certified) > 0:
            latest_time = max([c['cert_time'] for c in certified if c['cert_time']])
            sig_period = await self._blockchain_processor.parameters(currency).sig_period
            current_time = await self._blockchain_processor.time(self.currency)
            if current_time - latest_time < parameters['sigPeriod']:
                return parameters['sigPeriod'] - (current_time - latest_time)
        return 0

    async def update_memberships(self, identity):
        """
        Request the identity data and save it to written identities
        :param sakia.data.entities.Identity identity: the identity
        """
        if not identity.written_on:
            try:
                search = await self._bma_connector.get(self.currency, bma.blockchain.Membership,
                                                            {'search': self.pubkey})
                blockstamp = BlockUID.empty()
                membership_data = None

                for ms in search['memberships']:
                    if ms['blockNumber'] > blockstamp.number:
                        blockstamp = BlockUID(ms["blockNumber"], ms['blockHash'])
                        membership_data = ms
                if membership_data:
                    identity.membership_timestamp = await self._blockchain_processor.timestamp(blockstamp)
                    identity.membership_buid = blockstamp
                    identity.membership_type = ms["type"]
                    identity.membership_written_on = ms["written"]
                    await self.refresh_requirements(identity)
                    self._identities_processor.commit_identity(identity)
            except errors.DuniterError as e:
                logging.debug(str(e))
            except NoPeerAvailable as e:
                logging.debug(str(e))

    async def update_certified_by(self, identity):
        """
        Request the identity data and save it to written certifications
        :param sakia.data.entities.Identity identity: the identity
        """
        try:
            data = await self._bma_connector.get(self.currency, bma.wot.CertifiedBy, {'search': self.pubkey})
            for certified_data in data['certifications']:
                cert = Certification(self.currency, data["pubkey"],
                                     certified_data["pubkey"], certified_data["sigDate"])
                cert.block_number = certified_data["cert_time"]["number"]
                cert.timestamp = certified_data["cert_time"]["medianTime"]
                if certified_data['written']:
                    cert.written_on = BlockUID(certified_data['written']['number'],
                                               certified_data['written']['hash'])
                self._certs_processor.commit_certification(cert)
        except errors.DuniterError as e:
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                logging.debug("Certified by error : {0}".format(str(e)))
        except NoPeerAvailable as e:
            logging.debug(str(e))

    def _parse_revocations(self, block):
        """
        Parse revoked pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of pubkeys updated
        """
        revoked = set([])
        for rev in block.revoked:
            revoked.add(rev.pubkey)

        for pubkey in revoked:
            written = self._identities_processor.get_written(self.currency, pubkey)
            # we update every written identities known locally
            if written:
                written.revoked_on = block.blockUID
                written.member = False
        return revoked

    def _parse_memberships(self, block):
        """
        Parse memberships pubkeys found in a block and refresh local data

        :param duniterpy.documents.Block block: the block received
        :return: list of pubkeys requiring a refresh of requirements
        """
        need_refresh = []
        for ms in block.joiners + block.actives:
            written = self._identities_processor.get_written(self.currency, ms.issuer)
            # we update every written identities known locally
            if written:
                written.membership_written_on = block.blockUID
                written.membership_type = "IN"
                written.membership_buid = ms.membership_ts
                self._identities_processor.commit_identity(written)
                # If the identity was not member
                # it can become one
                if not written.member:
                    need_refresh.append(written)

        for ms in block.leavers:
            written = self._identities_processor.get_written(self.currency, ms.issuer)
            # we update every written identities known locally
            if written:
                written.membership_written_on = block.blockUID
                written.membership_type = "OUT"
                written.membership_buid = ms.membership_ts
                self._identities_processor.commit_identity(written)
                # If the identity was not member
                # it can stop to be one
                if not written.member:
                    need_refresh.append(written)
        return need_refresh

    def _parse_certifications(self, block):
        """
        Parse certified pubkeys found in a block and refresh local data
        This method only creates certifications if one of both identities is
        locally known as written.
        This method returns the identities needing to be refreshed. These can only be
        the identities which we already known as written before parsing this certification.
        :param duniterpy.documents.Block block:
        :return:
        """
        need_refresh = set([])
        for cert in block.certifications:
            written = self._identities_processor.get_written(self.currency, cert.pubkey_to)
            # if we have locally a written identity matching the certification
            if written or self._identities_processor.get_written(self.currency, cert.pubkey_from):
                self._certs_processor.create_certification(self.currency, cert, block.blockUID)
            # we update every written identities known locally
            if written:
                # A certification can change the requirements state
                # of an identity
                need_refresh.add(written)
        return need_refresh

    async def refresh_requirements(self, identity):
        """
        Refresh a given identity information
        :param sakia.data.entities.Identity identity:
        :return:
        """
        requirements = await self._bma_connector.get(self.currency, bma.wot.Requirements,
                                                     get_args={'search': identity.pubkey})
        identity_data = requirements['identities'][0]
        identity.uid = identity_data["uid"]
        identity.blockstamp = identity["meta"]["timestamp"]
        identity.member = identity["membershipExpiresIn"] > 0 and identity["outdistanced"] is False
        median_time = self._blockchain_processor.time(self.currency)
        expiration_time = self._blockchain_processor.parameters(self.currency).ms_validity
        identity.membership_timestamp = median_time - (expiration_time - identity["membershipExpiresIn"])
        self._identities_processor.commit_identity(identity)

    def parse_block(self, block):
        """
        Parse a block to refresh local data
        :param block:
        :return:
        """
        self._parse_revocations(block)
        need_refresh = []
        need_refresh += self._parse_memberships(block)
        need_refresh += self._parse_certifications(block)
        return set(need_refresh)

    async def handle_new_blocks(self, blocks):
        """
        Handle new block received and refresh local data
        :param duniterpy.documents.Block block: the received block
        """
        need_refresh = []
        for block in blocks:
            need_refresh += self.parse_block(block)
        refresh_futures = []
        # for every identity for which we need a refresh, we gather
        # requirements requests
        for identity in set(need_refresh):
            refresh_futures.append(self.refresh_requirements(identity))
        await asyncio.gather(refresh_futures)
