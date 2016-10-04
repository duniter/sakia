import attr
from ..entities import Identity
from duniterpy.api import bma, errors
import asyncio
from aiohttp.errors import ClientError
from sakia.errors import NoPeerAvailable
from duniterpy.documents import SelfCertification
from duniterpy import PROTOCOL_VERSION


@attr.s
class IdentitiesProcessor:
    _identities_repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

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

    def update_identity(self, identity):
        """
        Saves an identity state in the db
        :param sakia.data.entities.Identity identity: the identity updated
        """
        self._identities_repo.update(identity)
