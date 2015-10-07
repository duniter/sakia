from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from ucoinpy.api import bma
from .identity import Identity, LocalState, BlockchainState

import json
import asyncio
import logging
from aiohttp.errors import ClientError
from ...tools.exceptions import NoPeerAvailable


class IdentitiesRegistry:
    """
    Core class to handle identities lookup
    """
    def __init__(self, instances={}):
        """
        Initializer of the IdentitiesRegistry

        :param list of Identity instances:
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
        for currency in json_data['registry']:
            instances[currency] = {}
            for person_data in json_data['registry'][currency]:
                pubkey = person_data['pubkey']
                if pubkey not in instances:
                    person = Identity.from_json(person_data)
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
        :param  cutecoin.core.Community community: the community
        :return: The identities of the community
        :rtype: dict
        """
        try:
            return self._instances[community.currency]
        except KeyError:
            self._instances[community.currency] = {}
            return self._identities(community)

    @asyncio.coroutine
    def _find_by_lookup(self, pubkey, community):
        identity = self._identities(community)[pubkey]
        lookup_tries = 0
        while lookup_tries < 3:
            try:
                data = yield from community.bma_access.simple_request(bma.wot.Lookup,
                                                            req_args={'search': pubkey})
                timestamp = 0
                for result in data['results']:
                    if result["pubkey"] == identity.pubkey:
                        uids = result['uids']
                        identity_uid = ""
                        for uid_data in uids:
                            if uid_data["meta"]["timestamp"] > timestamp:
                                timestamp = uid_data["meta"]["timestamp"]
                                identity_uid = uid_data["uid"]
                                identity.uid = identity_uid
                                identity.blockchain_state = BlockchainState.BUFFERED
                                identity.local_state = LocalState.PARTIAL
                return identity
            except ValueError as e:
                lookup_tries += 1
            except asyncio.TimeoutError:
                lookup_tries += 1
            except ClientError:
                lookup_tries += 1
            except NoPeerAvailable:
                return identity
        return identity

    @asyncio.coroutine
    def future_find(self, pubkey, community):
        if pubkey in self._identities(community):
            identity = self._identities(community)[pubkey]
        else:
            identity = Identity.empty(pubkey)
            self._identities(community)[pubkey] = identity
            tries = 0
            while tries < 3 and identity.local_state == LocalState.NOT_FOUND:
                try:
                    data = yield from community.bma_access.simple_request(bma.wot.CertifiersOf,
                                                                          req_args={'search': pubkey})
                    identity.uid = data['uid']
                    identity.local_state = LocalState.PARTIAL
                    identity.blockchain_state = BlockchainState.VALIDATED
                except ValueError as e:
                    if '404' in str(e) or '400' in str(e):
                        identity = yield from self._find_by_lookup(pubkey, community)
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

    def from_handled_data(self, uid, pubkey, blockchain_state, community):
        """
        Get a person from a metadata dict.
        A metadata dict has a 'text' key corresponding to the person uid,
        and a 'id' key corresponding to the person pubkey.

        :param dict metadata: The person metadata
        :return: A new person if pubkey wasn't knwon, else the existing instance.
        """
        if pubkey in self._instances:
            if self._identities(community)[pubkey].blockchain_state == BlockchainState.NOT_FOUND:
                self._identities(community)[pubkey].blockchain_state = blockchain_state
            elif self._identities(community)[pubkey].blockchain_state != BlockchainState.VALIDATED \
                    and blockchain_state == BlockchainState.VALIDATED:
                self._identities(community)[pubkey].blockchain_state = blockchain_state

            # TODO: Random bug in ucoin makes the uid change without reason in requests answers
            # https://github.com/ucoin-io/ucoin/issues/149
            #if self._instances[pubkey].uid != uid:
            #    self._instances[pubkey].uid = uid
            #    self._instances[pubkey].inner_data_changed.emit("BlockchainState")

            if self._identities(community)[pubkey].local_state == LocalState.NOT_FOUND:
                self._identities(community)[pubkey].local_state = LocalState.COMPLETED

            return self._identities(community)[pubkey]
        else:
            identity = Identity.from_handled_data(uid, pubkey, blockchain_state)
            self._identities(community)[pubkey] = identity
            return identity
