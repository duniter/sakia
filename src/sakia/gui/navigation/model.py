from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
from sakia.models.generic_tree import GenericTreeModel
from sakia.data.processors import ConnectionsProcessor


class NavigationModel(QObject):
    """
    The model of Navigation component
    """
    navigation_changed = pyqtSignal(GenericTreeModel)

    def __init__(self, parent, app):
        """

        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app:
        """
        super().__init__(parent)
        self.app = app
        self.navigation = []
        self._current_data = None

    def init_navigation_data(self):
        self.navigation = [
            {
                'title': self.tr('Network'),
                'icon': ':/icons/network_icon',
                'component': "Network",
                'dependencies': {
                    'network_service': self.app.network_service,
                },
                'misc': {
                },
                'children': []
            }
        ]

        self._current_data = self.navigation[0]
        for connection in self.app.db.connections_repo.get_all():
            self.navigation[0]['children'].append(self.create_node(connection))
        return self.navigation

    def create_node(self, connection):
        node = {
            'title': connection.title(),
            'component': "Informations",
            'dependencies': {
                'blockchain_service': self.app.blockchain_service,
                'identities_service': self.app.identities_service,
                'sources_service': self.app.sources_service,
                'connection': connection,
            },
            'misc': {
                'connection': connection
            },
            'children': [
                {
                    'title': self.tr('Transfers'),
                    'icon': ':/icons/tx_icon',
                    'component': "TxHistory",
                    'dependencies': {
                        'connection': connection,
                        'identities_service': self.app.identities_service,
                        'blockchain_service': self.app.blockchain_service,
                        'transactions_service': self.app.transactions_service,
                        "sources_service": self.app.sources_service
                    },
                    'misc': {
                        'connection': connection
                    }
                }
            ]
        }
        if connection.uid:
            node["children"] += [{
                'title': self.tr('Identities'),
                'icon': ':/icons/members_icon',
                'component': "Identities",
                'dependencies': {
                    'connection': connection,
                    'blockchain_service': self.app.blockchain_service,
                    'identities_service': self.app.identities_service,
                },
                'misc': {
                    'connection': connection
                }
            },
            {
                'title': self.tr('Web of Trust'),
                'icon': ':/icons/wot_icon',
                'component': "Wot",
                'dependencies': {
                    'connection': connection,
                    'blockchain_service': self.app.blockchain_service,
                    'identities_service': self.app.identities_service,
                },
                'misc': {
                    'connection': connection
                }
            }]
        return node

    def generic_tree(self):
        return GenericTreeModel.create("Navigation", self.navigation)

    def add_connection(self, connection):
        raw_node = self.create_node(connection)
        self.navigation[0]["children"].append(raw_node)
        return raw_node

    def set_current_data(self, raw_data):
        self._current_data = raw_data

    def current_data(self, key):
        return self._current_data.get(key, None)

    def _lookup_raw_data(self, raw_data, component, **kwargs):
        if raw_data['component'] == component:
            for k in kwargs:
                if raw_data['misc'].get(k, None) == kwargs[k]:
                    return raw_data
        for c in raw_data.get('children', []):
            children_data = self._lookup_raw_data(c, component, **kwargs)
            if children_data:
                return children_data

    def get_raw_data(self, component, **kwargs):
        for data in self.navigation:
            return self._lookup_raw_data(data, component, **kwargs)

    def current_connection(self):
        if self._current_data:
            return self._current_data['misc'].get('connection', None)
        else:
            return None

    def generate_revokation(self, connection, secret_key, password):
        return self.app.documents_service.generate_revokation(connection, secret_key, password)

    def identity_published(self, connection):
        return self.app.identities_service.get_identity(connection.pubkey, connection.uid).written

    def identity_is_member(self, connection):
        return self.app.identities_service.get_identity(connection.pubkey, connection.uid).member

    async def remove_connection(self, connection):
        for data in self.navigation:
            connected_to = self._current_data['misc'].get('connection', None)
            if connected_to == connection:
                self._current_data['widget'].disconnect()
        await self.app.remove_connection(connection)

    async def send_leave(self, connection, secret_key, password):
        return await self.app.documents_service.send_membership(connection, secret_key, password, "OUT")

    async def send_identity(self, connection, secret_key, password):
        return await self.app.documents_service.broadcast_identity(connection, secret_key, password)

    @staticmethod
    def copy_pubkey_to_clipboard(connection):
        clipboard = QApplication.clipboard()
        clipboard.setText(connection.pubkey)