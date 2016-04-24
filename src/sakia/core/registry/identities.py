from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID
from .identity import Identity, LocalState, BlockchainState
from pkg_resources import parse_version
import asyncio
from aiohttp.errors import ClientError
from ...tools.exceptions import NoPeerAvailable


class IdentitiesRegistry:
    """
    Core class to handle identities lookup
    """
    def __init__(self, instances={}):
        """
        Initializer of the IdentitiesRegistry

        :param dict instances: A dictionary containing identities based on communities
        :return: An IdentitiesRegistry object
        :rtype: IdentitiesRegistry
        """
        self._instances = instances

    def load_json(self, json_data):
        """
        Load json data

        :param dict json_data: The identities in json format
        """
        instances = {}
        version = parse_version(json_data['version'])
        for currency in json_data['registry']:
            instances[currency] = {}
            for person_data in json_data['registry'][currency]:
                pubkey = person_data['pubkey']
                if pubkey not in instances:
                    person = Identity.from_json(person_data, version)
                    instances[currency][person.pubkey] = person
        self._instances = instances

    def jsonify(self):
        communities_json = {}
        for currency in self._instances:
            identities_json = []
            for identity in self._instances[currency].values():
                identities_json.append(identity.jsonify())
            communities_json[currency] = identities_json
        return {'registry': communities_json}

    def _identities(self, community):
        """
        If the registry do not have data for this community
        Create a new dict and return it
        :param  sakia.core.Community community: the community
        :return: The identities of the community
        :rtype: dict
        """
        try:
            return self._instances[community.currency]
        except KeyError:
            self._instances[community.currency] = {}
            return self._identities(community)

    async def _find_by_lookup(self, pubkey, community):
        identity = self._identities(community)[pubkey]
        lookup_tries = 0
        while lookup_tries < 3:
            try:
                data = await community.bma_access.simple_request(bma.wot.Lookup,
                                                            req_args={'search': pubkey})
                timestamp = BlockUID.empty()
                for result in data['results']:
                    if result["pubkey"] == identity.pubkey:
                        uids = result['uids']
                        for uid_data in uids:
                            if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                                identity.sigdate = BlockUID.from_str(uid_data["meta"]["timestamp"])
                                identity.uid = uid_data["uid"]
                                identity.blockchain_state = BlockchainState.BUFFERED
                                identity.local_state = LocalState.PARTIAL
                                timestamp = identity.sigdate
                return identity
            except errors.DuniterError as e:
                if e.ucode == errors.NO_MATCHING_IDENTITY:
                    lookup_tries += 1
            except asyncio.TimeoutError:
                lookup_tries += 1
            except ClientError:
                lookup_tries += 1
            except NoPeerAvailable:
                return identity
        return identity

    async def future_find(self, pubkey, community):
        """

        :param pubkey: The pubkey we look for
        :param community: The community where we look for the identity
        :return: The identity found
        :rtype: sakia.core.registry.Identity
        """
        if pubkey in self._identities(community):
            identity = self._identities(community)[pubkey]
        else:
            identity = Identity.empty(pubkey)
            self._identities(community)[pubkey] = identity
            tries = 0
            while tries < 3 and identity.local_state == LocalState.NOT_FOUND:
                try:
                    data = await community.bma_access.simple_request(bma.blockchain.Membership,
                                                                          req_args={'search': pubkey})
                    identity.uid = data['uid']
                    identity.sigdate = BlockUID.from_str(data['sigDate'])
                    identity.local_state = LocalState.PARTIAL
                    identity.blockchain_state = BlockchainState.VALIDATED
                except errors.DuniterError as e:
                    if errors.NO_MEMBER_MATCHING_PUB_OR_UID:
                        identity = await self._find_by_lookup(pubkey, community)
                        return identity
                    else:
                        tries += 1
                except asyncio.TimeoutError:
                    tries += 1
                except ClientError:
                    tries += 1
                except NoPeerAvailable:
                    return identity
        return identity

    def from_handled_data(self, uid, pubkey, sigdate, blockchain_state, community):
        """
        Get a person from a metadata dict.
        A metadata dict has a 'text' key corresponding to the person uid,
        and a 'id' key corresponding to the person pubkey.

        :param str uid: The person uid, also known as its uid on the network
        :param str pubkey: The person pubkey
        :param BlockUID sig_date: The date of signature of the self certification
        :param LocalState local_state: The local status of the identity
        :param sakia.core.Community community: The community from which we found data
        :rtype: sakia.core.registry.Identity
        """
        identities = self._identities(community)
        if pubkey in identities:
            if identities[pubkey].blockchain_state == BlockchainState.NOT_FOUND:
                identities[pubkey].blockchain_state = blockchain_state
            elif identities[pubkey].blockchain_state != BlockchainState.VALIDATED \
                    and blockchain_state == BlockchainState.VALIDATED:
                identities[pubkey].blockchain_state = blockchain_state

            if identities[pubkey].uid != uid:
                identities[pubkey].uid = uid

            if sigdate and identities[pubkey].sigdate != sigdate:
                identities[pubkey].sigdate = sigdate

            if identities[pubkey].local_state == LocalState.NOT_FOUND:
                identities[pubkey].local_state = LocalState.COMPLETED

            return identities[pubkey]
        else:
            identity = Identity.from_handled_data(uid, pubkey, sigdate, blockchain_state)
            self._identities(community)[pubkey] = identity
            return identity
