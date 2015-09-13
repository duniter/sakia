from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
from ucoinpy.api import bma
from .identity import Identity

import asyncio


class IdentitiesRegistry:
    def __init__(self, instances={}):
        pass

    def load_json(self, json_data):
        pass

    def jsonify(self):
        return {'registry': []}

    def lookup(self, pubkey, community):
        identity = Identity.empty(pubkey)
        return identity

    @asyncio.coroutine
    def future_find(self, pubkey, community):
        identity = Identity.empty(pubkey)
        yield from asyncio.sleep(1)
        return identity

    def from_metadata(self, metadata):
        return Identity()
