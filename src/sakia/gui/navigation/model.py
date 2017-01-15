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
        currencies = ConnectionsProcessor.instanciate(self.app).currencies()
        if currencies:
            self.navigation = [
                {
                    'title': self.tr('Network'),
                    'icon': ':/icons/network_icon',
                    'component': "Network",
                    'dependencies': {
                        'network_service': self.app.network_services[currencies[0]],
                    },
                    'misc': {
                    },
                    'children': []
                }
            ]
        else:
            self.navigation = [
                {
                    'title': self.tr("No connection configured"),
                    'component': "HomeScreen",
                    'parameters': self.app.parameters,
                    'dependencies': {},
                    'misc': {},
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
                'blockchain_service': self.app.blockchain_services[connection.currency],
                'identities_service': self.app.identities_services[connection.currency],
                'sources_service': self.app.sources_services[connection.currency],
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
                        'identities_service': self.app.identities_services[connection.currency],
                        'blockchain_service': self.app.blockchain_services[connection.currency],
                        'transactions_service': self.app.transactions_services[connection.currency],
                        "sources_service": self.app.sources_services[connection.currency]
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
                    'blockchain_service': self.app.blockchain_services[connection.currency],
                    'identities_service': self.app.identities_services[connection.currency],
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
                    'blockchain_service': self.app.blockchain_services[connection.currency],
                    'identities_service': self.app.identities_services[connection.currency],
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

    def current_connection(self):
        if self._current_data:
            return self._current_data['misc'].get('connection', None)
        else:
            return None

    def generate_revokation(self, connection, password):
        return self.app.documents_service.generate_revokation(connection, password)

    def identity_published(self, connection):
        identities_services = self.app.identities_services[connection.currency]
        return identities_services.get_identity(connection.pubkey, connection.uid).written

    def identity_is_member(self, connection):
        identities_services = self.app.identities_services[connection.currency]
        return identities_services.get_identity(connection.pubkey, connection.uid).member

    async def remove_connection(self, connection):
        await self.app.remove_connection(connection)

    async def send_leave(self, connection, password):
        return await self.app.documents_service.send_membership(connection, password, "OUT")

    @staticmethod
    def copy_pubkey_to_clipboard(connection):
        clipboard = QApplication.clipboard()
        clipboard.setText(connection.pubkey)