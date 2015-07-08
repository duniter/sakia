from PyQt5.QtNetwork import QNetworkReply
from cutecoin.core.net.api import bma as qtbma
from .identity import Identity

import json
import asyncio
import logging


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

    def lookup(self, pubkey, community):
        """
        Get a person from the pubkey found in a community

        :param str pubkey: The person pubkey
        :param cutecoin.core.community.Community community: The community in which to look for the pubkey
        :param bool cached: True if the person should be searched in the
        cache before requesting the community.

        :return: A new person if the pubkey was unknown or\
        the known instance if pubkey was already known.
        :rtype: cutecoin.core.registry.Identity
        """
        if pubkey in self._instances:
            identity = self._instances[pubkey]
            self._instances[pubkey] = identity
        else:
            identity = Identity.empty(pubkey)
            self._instances[pubkey] = identity
            reply = community.bma_access.simple_request(qtbma.wot.Lookup, req_args={'search': pubkey})
            reply.finished.connect(lambda: self.handle_lookup(reply, identity, community))
        return identity

    @asyncio.coroutine
    def future_lookup(self, pubkey, community):
        def handle_reply(reply):
            strdata = bytes(reply.readAll()).decode('utf-8')
            data = json.loads(strdata)

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
                    identity.status = Identity.FOUND
                    logging.debug("Lookup : found {0}".format(identity))
                    future_identity.set_result(True)
                    return
            future_identity.set_result(True)

        future_identity = asyncio.Future()
        if pubkey in self._instances:
            identity = self._instances[pubkey]
            future_identity.set_result(True)
        else:
            identity = Identity.empty(pubkey)
            self._instances[pubkey] = identity
            reply = community.bma_access.simple_request(qtbma.wot.Lookup, req_args={'search': pubkey})
            reply.finished.connect(lambda: handle_reply(reply))
        yield from future_identity
        return identity

    def handle_lookup(self, reply, identity, community, tries=0):
        """
        :param cutecoin.core.registry.identity.Identity identity: The looked up identity
        :return:
        """

        if reply.error() == QNetworkReply.NoError:
            strdata = bytes(reply.readAll()).decode('utf-8')
            data = json.loads(strdata)

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
                    identity.status = Identity.FOUND
                    logging.debug("Lookup : found {0}".format(identity))
                    identity.inner_data_changed.emit(str(qtbma.wot.Lookup))
        else:
            logging.debug("Error in reply : {0}".format(reply.error()))
            if tries < 3:
                tries += 1
                reply = community.bma_access.simple_request(qtbma.wot.Lookup,
                                                            req_args={'search': identity.pubkey})
                reply.finished.connect(lambda: self.handle_lookup(reply, identity,
                                                                  community, tries=tries))

    def from_metadata(self, metadata):
        """
        Get a person from a metadata dict.
        A metadata dict has a 'text' key corresponding to the person uid,
        and a 'id' key corresponding to the person pubkey.

        :param dict metadata: The person metadata
        :return: A new person if pubkey wasn't knwon, else the existing instance.
        """
        pubkey = metadata['id']
        if pubkey in self._instances:
            return self._instances[pubkey]
        else:
            identity = Identity.from_metadata(metadata)
            self._instances[pubkey] = identity
            return identity
