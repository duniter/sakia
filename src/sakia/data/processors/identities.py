import attr
import sqlite3
import logging
import asyncio
from ..entities import Identity
from ..connectors import BmaConnector
from ..processors import NodesProcessor
from duniterpy.api import bma, errors
from duniterpy.key import SigningKey
from duniterpy.documents import Identity, BlockUID, block_uid
from aiohttp.errors import ClientError
from sakia.errors import NoPeerAvailable


@attr.s
class IdentitiesProcessor:
    _identities_repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
    _blockchain_repo = attr.ib()  # :type sakia.data.repositories.BlockchainRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.identities_repo, app.db.blockchains_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo)))

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
                            identity.blockstamp = data['meta']['timestamp']
                            identity.signature = data['self']
                            if identity not in identities:
                                identities.append(identity)
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
                data = await self._bma_connector.get(currency, bma.wot.Lookup, req_args={'search': text})
                for result in data['results']:
                    pubkey = result['pubkey']
                    for uid_data in result['uids']:
                        if not uid_data['revoked']:
                            identity = Identity(currency, pubkey, uid_data['uid'],
                                                uid_data['meta']['timestamp'], uid_data['self'])
                            if identity not in identities:
                                identities.append(identity)
                break
            except (errors.DuniterError, asyncio.TimeoutError, ClientError) as e:
                tries += 1
            except NoPeerAvailable as e:
                self._logger.debug(str(e))
        return identities

    def get_written(self, currency, pubkey):
        """
        Get identities from a given certification document
        :param str currency: the currency in which to look for written identities
        :param str pubkey: the pubkey of the identity

        :rtype: sakia.data.entities.Identity
        """
        return self._identities_repo.get_written(currency=currency, pubkey=pubkey)

    def get_identity(self, currency, pubkey, uid=""):
        """
        Return the identity corresponding to a given pubkey, uid and currency
        If no UID is given, o
        :param str currency:
        :param str pubkey:
        :param str uid: optionally, specify an uid to lookup

        :rtype: sakia.data.entities.Identity
        """
        written = self.get_written(currency=currency, pubkey=pubkey)
        if not written:
            identities = self._identities_repo.get_all(currency=currency, pubkey=pubkey)
            if identities:
                recent = identities[0]
                for i in identities:
                    if i.blockstamp > recent.blockstamp:
                        if uid and i.uid == uid:
                            recent = i
                        elif not uid:
                            recent = i
                return recent
        else:
            return written[0]

    def commit_identity(self, identity):
        """
        Saves an identity state in the db
        :param sakia.data.entities.Identity identity: the identity updated
        """
        try:
            self._identities_repo.insert(identity)
        except sqlite3.IntegrityError:
            self._identities_repo.update(identity)

    async def initialize_identity(self, identity, log_stream):
        """
        Initialize memberships and other data for given identity
        :param sakia.data.entities.Identity identity:
        :param function log_stream:
        """
        log_stream("Requesting membership data")
        memberships_data = await self._bma_connector.get(identity.currency, bma.blockchain.Membership,
                                                         req_args={'search': identity.pubkey})
        if block_uid(memberships_data['sigDate']) == identity.blockstamp \
           and memberships_data['uid'] == identity.uid:
            for ms in memberships_data['memberships']:
                if block_uid(ms['written']) > identity.membership_written_on:
                    identity.membership_buid = BlockUID(ms['blockNumber'], ms['blockHash'])
                    identity.membership_type = ms['membership']

            if identity.membership_buid:
                log_stream("Requesting membership timestamp")
                ms_block_data = await self._bma_connector.get(identity.currency, bma.blockchain.Block,
                                                              req_args={'number': identity.membership_buid.number})
                if ms_block_data:
                    identity.membership_timestamp = ms_block_data['medianTime']

            if memberships_data['memberships']:
                log_stream("Requesting identity requirements status")

                requirements_data = await self._bma_connector.get(identity.currency, bma.wot.Requirements,
                                                                  get_args={'search': identity.pubkey})
                identity.member = requirements_data['membershipExpiresIn'] > 0 and not requirements_data['outdistanced']

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
        selfcert = Identity(2,
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

        return result, identity
