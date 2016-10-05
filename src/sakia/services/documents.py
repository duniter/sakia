import asyncio
import attr
import logging
import jsonschema
from collections import Counter

from duniterpy.key import SigningKey
from duniterpy import PROTOCOL_VERSION
from duniterpy.documents import BlockUID, Block, SelfCertification, Certification, Membership, Revocation
from duniterpy.api import bma, errors
from sakia.data.entities import Node
from aiohttp.errors import ClientError, DisconnectedError


@attr.s()
class DocumentsService:
    """
    A service to forge and broadcast documents
    to the network
    """
    _bma_connector = attr.ib()  # :type: sakia.data.connectors.BmaConnector
    _blockchain_processor = attr.ib()  # :type: sakia.data.processors.BlockchainProcessor
    _identities_processor = attr.ib()  # :type: sakia.data.processors.IdentitiesProcessor
    _logger = attr.ib(default=lambda: logging.getLogger('sakia'))

    async def send_selfcert(self, currency, salt, password):
        """
        Send our self certification to a target community

        :param str currency: The currency of the identity
        :param sakia.data.entities.Identity identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        try:
            block_data = await self._bma_connector.get(currency, bma.blockchain.Current)
            signed_raw = "{0}{1}\n".format(block_data['raw'], block_data['signature'])
            block_uid = Block.from_signed_raw(signed_raw).blockUID
        except errors.DuniterError as e:
            if e.ucode == errors.NO_CURRENT_BLOCK:
                block_uid = BlockUID.empty()
            else:
                raise
        selfcert = SelfCertification(PROTOCOL_VERSION,
                                     currency,
                                     self.pubkey,
                                     self.name,
                                     block_uid,
                                     None)
        key = SigningKey(salt, password)
        selfcert.sign([key])
        self._logger.debug("Key publish : {0}".format(selfcert.signed_raw()))

        responses = await self._bma_connector.broadcast(currency, bma.wot.Add, {}, {'identity': selfcert.signed_raw()})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def send_membership(self, currency, identity, salt, password, mstype):
        """
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param str currency: the currency target
        :param sakia.data.entities.Identity identity: the identitiy data
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        """
        self._logger.debug("Send membership")

        blockUID = self._blockchain_processor.current_buid(currency)
        membership = Membership(PROTOCOL_VERSION, currency,
                                identity.pubkey, blockUID, mstype, identity.uid,
                                identity.timestamp, None)
        key = SigningKey(salt, password)
        membership.sign([key])
        self._logger.debug("Membership : {0}".format(membership.signed_raw()))
        responses = await self._bma_connector.broadcast(currency, bma.blockchain.Membership, {},
                                                            {'membership': membership.signed_raw()})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def certify(self, currency, identity, salt, password):
        """
        Certify an other identity

        :param str currency: The currency of the identity
        :param sakia.data.entities.Identity identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        self._logger.debug("Certdata")
        blockUID = self._blockchain_processor.current_buid(currency)

        certification = Certification(PROTOCOL_VERSION, currency,
                                      self.pubkey, identity.pubkey, blockUID, None)

        key = SigningKey(salt, password)
        certification.sign(identity.self_certification(), [key])
        signed_cert = certification.signed_raw(identity.self_certification())
        self._logger.debug("Certification : {0}".format(signed_cert))

        responses = await self._bma_connector.bma_access.broadcast(currency, bma.wot.Certify, {},
                                                                   {'cert': signed_cert})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
                # signal certification to all listeners
                self.certification_accepted.emit()
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def revoke(self, currency, identity, salt, password):
        """
        Revoke self-identity on server, not in blockchain

        :param str currency: The currency of the identity
        :param sakia.data.entities.Identity identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        revocation = Revocation(PROTOCOL_VERSION, currency, None)
        self_cert = identity.self_certification()

        key = SigningKey(salt, password)
        revocation.sign(self_cert, [key])

        self._logger.debug("Self-Revokation Document : \n{0}".format(revocation.raw(self_cert)))
        self._logger.debug("Signature : \n{0}".format(revocation.signatures[0]))

        data = {
            'pubkey': identity.pubkey,
            'self_': self_cert.signed_raw(),
            'sig': revocation.signatures[0]
        }
        self._logger.debug("Posted data : {0}".format(data))
        responses = await self._bma_connector.broadcast(currency, bma.wot.Revoke, {}, data)
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    async def generate_revokation(self, currency, identity, salt, password):
        """
        Generate account revokation document for given community

        :param str currency: The currency of the identity
        :param sakia.data.entities.Identity identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        document = Revocation(PROTOCOL_VERSION, currency, identity.pubkey, "")
        self_cert = identity.self_certification()

        key = SigningKey(salt, password)

        document.sign(self_cert, [key])
        return document.signed_raw(self_cert)
