from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from ucoinpy.api import bma
from .identity import Identity, LocalState, BlockchainState

import json
import asyncio
import logging
from aiohttp.errors import ClientError


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

        for person_data in json_data['registry']:
            pubkey = person_data['pubkey']
            if pubkey not in instances:
                person = Identity.from_json(person_data)
                instances[person.pubkey] = person
        self._instances = instances

    def jsonify(self):
        identities_json = []
        for identity in self._instances.values():
            identities_json.append(identity.jsonify())
        return {'registry': identities_json}

    @asyncio.coroutine
    def future_find(self, pubkey, community):
        def lookup():
            identity = Identity.empty(pubkey)
            self._instances[pubkey] = identity
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
                            logging.debug("Lookup : found {0}".format(identity))
                    return identity
                except ValueError as e:
                    lookup_tries += 1
                except ClientError:
                    lookup_tries += 1
            return identity

        if pubkey in self._instances:
            identity = self._instances[pubkey]
        else:
            identity = Identity.empty(pubkey)
            self._instances[pubkey] = identity
            tries = 0
            while tries < 3:
                try:
                    data = yield from community.bma_access.simple_request(bma.wot.CertifiersOf, req_args={'search': pubkey})
                    identity.uid = data['uid']
                    identity.local_state = LocalState.PARTIAL
                    identity.blockchain_state = BlockchainState.VALIDATED
                    return identity
                except ValueError as e:
                    if '404' in str(e):
                        return (yield from lookup())
                    else:
                        tries += 1
                except ClientError:
                    tries += 1
        return identity

    def from_handled_data(self, uid, pubkey, blockchain_state):
        """
        Get a person from a metadata dict.
        A metadata dict has a 'text' key corresponding to the person uid,
        and a 'id' key corresponding to the person pubkey.

        :param dict metadata: The person metadata
        :return: A new person if pubkey wasn't knwon, else the existing instance.
        """
        if pubkey in self._instances:
            if self._instances[pubkey].blockchain_state == BlockchainState.NOT_FOUND:
                self._instances[pubkey].blockchain_state = blockchain_state
            elif self._instances[pubkey].blockchain_state != BlockchainState.VALIDATED \
                    and blockchain_state == BlockchainState.VALIDATED:
                self._instances[pubkey].blockchain_state = blockchain_state
                self._instances[pubkey].inner_data_changed.emit("BlockchainState")

            # TODO: Random bug in ucoin makes the uid change without reason in requests answers
            # https://github.com/ucoin-io/ucoin/issues/149
            #if self._instances[pubkey].uid != uid:
            #    self._instances[pubkey].uid = uid
            #    self._instances[pubkey].inner_data_changed.emit("BlockchainState")

            if self._instances[pubkey].local_state == LocalState.NOT_FOUND:
                self._instances[pubkey].local_state = LocalState.COMPLETED

            return self._instances[pubkey]
        else:
            identity = Identity.from_handled_data(uid, pubkey, blockchain_state)
            self._instances[pubkey] = identity
            return identity
