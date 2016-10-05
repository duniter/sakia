import attr
import sqlite3
import logging
import asyncio
from ..entities import Identity
from duniterpy.api import bma, errors
from aiohttp.errors import ClientError
from sakia.errors import NoPeerAvailable
from duniterpy.documents import BlockUID


@attr.s
class IdentitiesProcessor:
    _identities_repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
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
        return self._identities_repo.get_written(**{'currency': currency, 'pubkey': pubkey})

    def commit_identity(self, identity):
        """
        Saves an identity state in the db
        :param sakia.data.entities.Identity identity: the identity updated
        """
        try:
            self._identities_repo.insert(identity)
        except sqlite3.IntegrityError:
            self._identities_repo.update(identity)

    async def check_registered(self, currency, identity):
        """
        Checks for the pubkey and the uid of an account in a community
        :param str currency: The currency we check for registration
        :param sakia.data.entities.Identity identity: the identity we check for registration
        :return: (True if found, local value, network value)
        """

        def _parse_uid_certifiers(data):
            return identity.uid == data['uid'], identity.uid, data['uid']

        def _parse_uid_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            for result in data['results']:
                if result["pubkey"] == identity.pubkey:
                    uids = result['uids']
                    for uid_data in uids:
                        if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                            timestamp = uid_data["meta"]["timestamp"]
                            found_uid = uid_data["uid"]
            return identity.uid == found_uid, identity.uid, found_uid

        def _parse_pubkey_certifiers(data):
            return identity.pubkey == data['pubkey'], identity.pubkey, data['pubkey']

        def _parse_pubkey_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            found_result = ["", ""]
            for result in data['results']:
                uids = result['uids']
                for uid_data in uids:
                    if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                        timestamp = BlockUID.from_str(uid_data["meta"]["timestamp"])
                        found_uid = uid_data["uid"]
                if found_uid == identity.uid:
                    found_result = result['pubkey'], found_uid
            if found_result[1] == identity.uid:
                return identity.pubkey == found_result[0], identity.pubkey, found_result[0]
            else:
                return False, identity.pubkey, None

        async def execute_requests(parsers, search):
            tries = 0
            request = bma.wot.CertifiersOf
            nonlocal registered
            # TODO: The algorithm is quite dirty
            # Multiplying the tries without any reason...
            while tries < 3 and not registered[0] and not registered[2]:
                try:
                    data = await self._bma_connector.get(currency, request, req_args={'search': search})
                    if data:
                        registered = parsers[request](data)
                    tries += 1
                except errors.DuniterError as e:
                    if e.ucode in (errors.NO_MEMBER_MATCHING_PUB_OR_UID,
                                   e.ucode == errors.NO_MATCHING_IDENTITY):
                        if request == bma.wot.CertifiersOf:
                            request = bma.wot.Lookup
                            tries = 0
                        else:
                            tries += 1
                    else:
                        tries += 1

        registered = (False, identity.uid, None)
        # We execute search based on pubkey
        # And look for account UID
        uid_parsers = {
            bma.wot.CertifiersOf: _parse_uid_certifiers,
            bma.wot.Lookup: _parse_uid_lookup
        }
        await execute_requests(uid_parsers, identity.pubkey)

        # If the uid wasn't found when looking for the pubkey
        # We look for the uid and check for the pubkey
        if not registered[0] and not registered[2]:
            pubkey_parsers = {
                bma.wot.CertifiersOf: _parse_pubkey_certifiers,
                bma.wot.Lookup: _parse_pubkey_lookup
            }
            await execute_requests(pubkey_parsers, identity.uid)

        return registered
