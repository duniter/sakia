import attr
from ..entities import Identity
from duniterpy.api import bma, errors
import asyncio
from aiohttp.errors import ClientError
from sakia.errors import NoPeerAvailable


@attr.s
class IdentityProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

    async def find_from_pubkey(self, currency, pubkey):
        """
        Get the list of identities corresponding to a pubkey
        from the network and the local db
        :param currency:
        :param pubkey:
        :rtype: list[sakia.data.entities.Identity]
        """
        identities = self._repo.get_all(currency=currency, pubkey=pubkey)
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
                                self._repo.insert(identity)
            except (errors.DuniterError, asyncio.TimeoutError, ClientError) as e:
                tries += 1
            except NoPeerAvailable:
                return identities
        return identities
