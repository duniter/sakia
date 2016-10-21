import attr
import sqlite3
import logging
import asyncio
from ..entities import Identity
from duniterpy.api import bma, errors
from duniterpy import PROTOCOL_VERSION
from duniterpy.key import SigningKey
from duniterpy.documents import SelfCertification, BlockUID
from aiohttp.errors import ClientError
from sakia.errors import NoPeerAvailable


@attr.s
class IdentitiesProcessor:
    _identities_repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
    _blockchain_repo = attr.ib()  # :type sakia.data.repositories.BlockchainRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    async def find_from_pubkey(self, currency, pubkey):
        """
        Get the list of identities corresponding to a pubkey
        from the network and the local db
        :param currency:
        :param pubkey:
        :rtype: list[sakia.data.entities.Identity]
        """
        identities = self._identities_repo.get_all(currency=currency, pubkey=pubkey)
        tries = 0
        while tries < 3:
            try:
                data = await self._bma_connector.get(bma.wot.Lookup,
                                                             req_args={'search': pubkey})
                for result in data['results']:
                    if result["pubkey"] == pubkey:
                        uids = result['uids']
                        for uid_data in uids:
                            identity = Identity(currency, pubkey)
                            identity.uid = uid_data['uid']
                            identity.blockstamp = data['sigDate']
                            identity.signature = data['self']
                            if identity not in identities:
                                identities.append(identity)
                                self._identities_repo.insert(identity)
            except (errors.DuniterError, asyncio.TimeoutError, ClientError) as e:
                tries += 1
                self._logger.debug(str(e))
            except NoPeerAvailable:
                return identities
        return identities

    async def lookup(self, currency, text):
        """
        Get the list of identities corresponding to a pubkey
        from the network and the local db
        :param str currency:
        :param str text: the text to lookup
        :rtype: list[sakia.data.entities.Identity]
        """
        identities = self._identities_repo.find_all(currency=currency, text=text)
        tries = 0
        while tries < 3:
            try:
                data = await self._bma_connector.get(bma.wot.Lookup,
                                                             req_args={'search': text})
                for result in data['results']:
                    pubkey = result['pubkey']
                    for uid_data in result['uids']:
                        identity = Identity(currency, pubkey, uid_data['uid'], uid_data['sigDate'])
                        identity.signature = data['self']
                        if identity not in identities:
                            identities.append(identity)
                            self._identities_repo.insert(identity)
            except (errors.DuniterError, asyncio.TimeoutError, ClientError) as e:
                tries += 1
            except NoPeerAvailable:
                return identities
        return identities

    def get_written(self, currency, pubkey):
        """
        Get identities from a given certification document
        :param str currency: the currency in which to look for written identities
        :param str pubkey: the pubkey of the identity

        :rtype: sakia.data.entities.Identity
        """
        return self._identities_repo.get_written(currency=currency, pubkey=pubkey)

    def get_identity(self, currency, pubkey, uid):
        """
        Return the identity corresponding to a given pubkey, uid and currency
        :param str currency:
        :param str pubkey:
        :param str uid:

        :rtype: sakia.data.entities.Identity
        """
        written = self.get_written(currency=currency, pubkey=pubkey)
        if not written:
            identities = self._identities_repo.get_all(currency=currency, pubkey=pubkey, uid=uid)
            recent = identities[0]
            for i in identities:
                if i.blockstamp > recent.blockstamp:
                    recent = i
            return recent

    def commit_identity(self, identity):
        """
        Saves an identity state in the db
        :param sakia.data.entities.Identity identity: the identity updated
        """
        try:
            self._identities_repo.insert(identity)
        except sqlite3.IntegrityError:
            self._identities_repo.update(identity)

    async def publish_selfcert(self, currency, identity, salt, password):
        """
        Send our self certification to a target community
        :param sakia.data.entities.Identity identity: The identity broadcasted
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        :param str currency: The currency target of the self certification
        """
        blockchain = self._blockchain_repo.get_one(currency=currency)
        block_uid = blockchain.current_buid
        timestamp = blockchain.median_time
        selfcert = SelfCertification(2,
                                     currency,
                                     identity.pubkey,
                                     identity.uid,
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

        if result[0]:
            identity.blockstamp = block_uid
            identity.signature = selfcert.signatures[0]
            identity.timestamp = timestamp

        self.commit_identity(identity)

        return result