from PyQt5.QtCore import QObject
import asyncio
from duniterpy.api import bma


class IdentitiesService(QObject):
    """
    Identities service is managing identities data received
    to update data locally
    """
    def __init__(self, currency, identities_processor, certs_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor for given currency
        :param sakia.data.processors.CertificationsProcessor certs_processor: the certifications processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._identities_processor = identities_processor
        self._certs_processor = certs_processor
        self._bma_connector = bma_connector
        self.currency = currency

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
            written = self._identities_processor.get_written(pubkey)
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
            written = self._identities_processor.get_written(ms.issuer)
            # we update every written identities known locally
            if written:
                written.membership_written_on = block.blockUID
                written.membership_type = "IN"
                written.membership_buid = ms.membership_ts
                self._identities_processor.update_identity(written)
                # If the identity was not member
                # it can become one
                if not written.member:
                    need_refresh.append(written)

        for ms in block.leavers:
            written = self._identities_processor.get_written(ms.issuer)
            # we update every written identities known locally
            if written:
                written.membership_written_on = block.blockUID
                written.membership_type = "OUT"
                written.membership_buid = ms.membership_ts
                self._identities_processor.update_identity(written)
                # If the identity was not member
                # it can stop to be one
                if not written.member:
                    need_refresh.append(written)
        return need_refresh

    def _parse_certifications(self, block):
        """
        Parse certified pubkeys found in a block and refresh local data
        :param duniterpy.documents.Block block:
        :return:
        """
        need_refresh = set([])
        for cert in block.certifications:
            written = self._identities_processor.get_written(cert.pubkey_to)
            # if we have locally a written identity matching the certification
            if written or self._identities_processor.get_written(cert.pubkey_from):
                self._certs_processor.create_certification(cert, block.blockUID)
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
        requirements = await self._bma_connector.get(bma.wot.Requirements, get_args={'search': identity.pubkey})
        identity_data = requirements['identities'][0]
        identity.uid = identity_data["uid"]
        identity.blockstamp = identity["meta"]["timestamp"]
        identity.member = identity["membershipExpiresIn"] > 0 and identity["outdistanced"] is False
        self._identities_processor.update_identity(identity)

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
