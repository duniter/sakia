"""
Created on 11 févr. 2014

@author: inso
"""

import logging
import time
import asyncio

from ucoinpy.documents.certification import SelfCertification
from cutecoin.tools.exceptions import Error, NoPeerAvailable,\
                                        MembershipNotFoundError
from cutecoin.core.net.api import bma as qtbma
from cutecoin.core.net.api.bma import PROTOCOL_VERSION
from PyQt5.QtCore import QObject, pyqtSignal


class Identity(QObject):
    """
    A person with a uid and a pubkey
    """
    FOUND = 1
    NOT_FOUND = 0

    inner_data_changed = pyqtSignal(str)

    def __init__(self, uid, pubkey, status):
        """
        Initializing a person object.

        :param str uid: The person uid, also known as its uid on the network
        :param str pubkey: The person pubkey
        :param int status: The local status of the identity
        """
        super().__init__()
        assert(status in (Identity.FOUND, Identity.NOT_FOUND))
        self.uid = uid
        self.pubkey = pubkey
        self.status = status

    @classmethod
    def empty(cls, pubkey):
        return cls("", pubkey, Identity.NOT_FOUND)

    @classmethod
    def from_metadata(cls, metadata):
        return cls(metadata["text"], metadata["id"], Identity.NOT_FOUND)

    @classmethod
    def from_json(cls, json_data):
        """
        Create a person from json data

        :param dict json_data: The person as a dict in json format
        :return: A new person if pubkey wasn't known, else a new person instance.
        """
        pubkey = json_data['pubkey']
        uid = json_data['uid']
        status = json_data['status']

        return cls(uid, pubkey, status)

    @asyncio.coroutine
    def selfcert(self, community):
        yield from asyncio.sleep(1)
        return None

    def get_join_date(self, community):
        return time.time() + 100000000

    def get_expiration_date(self, community):
        return time.time() + 1000000000

    def membership(self, community):
        raise MembershipNotFoundError()

    def published_uid(self, community):
        return False

    def is_member(self, community):
        return False

    def certifiers_of(self, community):
        return list()

    def unique_valid_certifiers_of(self, community):
        return list()

    def certified_by(self, community):
        return list()

    def unique_valid_certified_by(self, community):
        return list()

    def membership_expiration_time(self, community):
        current_time = time.time()
        return current_time+1000000

    def jsonify(self):
        """
        Get the community as dict in json format.
        :return: The community as a dict in json format
        """
        data = {'uid': self.uid,
                'pubkey': self.pubkey,
                'status': self.status}
        return data

    def __str__(self):
        status_str = ("NOT_FOUND", "FOUND")
        return "{0} - {1} - {2}".format(self.uid,
                                        self.pubkey,
                                        status_str[self.status])