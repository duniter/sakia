from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
from sakia.models.generic_tree import GenericTreeModel
from sakia.data.processors import ContactsProcessor
from duniterpy.documents.crc_pubkey import CRCPubkey


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
        self._contacts_processor = ContactsProcessor.instanciate(self.app)

    def handle_identity_change(self, identity):
        for node in self.navigation[3]['children']:
            if node['component'] == "Informations":
                connection = node["misc"]["connection"]
                if connection.pubkey == identity.pubkey and connection.uid == identity.uid:
                    icon = self.identity_icon(connection)
                    node["icon"] = icon
                    return node

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
            },
            {
                'title': self.tr('Identities'),
                'icon': ':/icons/members_icon',
                'component': "Identities",
                'dependencies': {
                    'blockchain_service': self.app.blockchain_service,
                    'identities_service': self.app.identities_service,
                },
                'misc': {
                }
            },
            {
                'title': self.tr('Web of Trust'),
                'icon': ':/icons/wot_icon',
                'component': "Wot",
                'dependencies': {
                    'blockchain_service': self.app.blockchain_service,
                    'identities_service': self.app.identities_service,
                },
                'misc': {
                }
            },
            {
                'title': self.tr('Personal accounts'),
                'children': []
            }
        ]

        self._current_data = self.navigation[0]
        for connection in self.app.db.connections_repo.get_all():
            self.navigation[3]['children'].append(self.create_node(connection))
        try:
            self._current_data = self.navigation[0]
        except IndexError:
            self._current_data = None
        return self.navigation

    def create_node(self, connection):
        matching_contact = self._contacts_processor.get_one(pubkey=connection.pubkey)
        if matching_contact:
            title = matching_contact.displayed_text()
        else:
            title = connection.title()
        if connection.uid:
            node = {
                'title': title,
                'component': "Informations",
                'icon': self.identity_icon(connection),
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
        else:
            node = {
                'title': title,
                'component': "TxHistory",
                'icon': ':/icons/tx_icon',
                'dependencies': {
                    'connection': connection,
                    'identities_service': self.app.identities_service,
                    'blockchain_service': self.app.blockchain_service,
                    'transactions_service': self.app.transactions_service,
                    "sources_service": self.app.sources_service
                },
                'misc': {
                    'connection': connection
                },
                'children': []
            }

        return node

    def identity_icon(self, connection):
        if self.identity_is_member(connection):
            return ':/icons/member'
        else:
            return ':/icons/not_member'

    def view_in_wot(self, connection):
        identity = self.app.identities_service.get_identity(connection.pubkey, connection.uid)
        self.app.view_in_wot.emit(identity)

    def generic_tree(self):
        return GenericTreeModel.create("Navigation", self.navigation[3]['children'])

    def add_connection(self, connection):
        raw_node = self.create_node(connection)
        self.navigation[3]["children"].append(raw_node)
        return raw_node

    def set_current_data(self, raw_data):
        self._current_data = raw_data

    def current_data(self, key):
        return self._current_data.get(key, None)

    def _lookup_raw_data(self, raw_data, component, **kwargs):
        if raw_data['component'] == component:
            if kwargs:
                for k in kwargs:
                    if raw_data['misc'].get(k, None) == kwargs[k]:
                        return raw_data
            else:
                return raw_data
        for c in raw_data.get('children', []):
            children_data = self._lookup_raw_data(c, component, **kwargs)
            if children_data:
                return children_data

    def get_raw_data(self, component, **kwargs):
        for data in self.navigation:
            raw_data = self._lookup_raw_data(data, component, **kwargs)
            if raw_data:
                return raw_data

    def current_connection(self):
        if self._current_data:
            return self._current_data['misc'].get('connection', None)
        else:
            return None

    def generate_revocation(self, connection, secret_key, password):
        return self.app.documents_service.generate_revocation(connection, secret_key, password)

    def identity_published(self, connection):
        identity = self.app.identities_service.get_identity(connection.pubkey, connection.uid)
        if identity:
            return identity.written
        else:
            return False

    def identity_is_member(self, connection):
        identity = self.app.identities_service.get_identity(connection.pubkey, connection.uid)
        if identity:
            return identity.member
        else:
            return False

    async def remove_connection(self, connection):
        for data in self.navigation:
            connected_to = self._current_data['misc'].get('connection', None)
            if connected_to == connection:
                try:
                    self._current_data['widget'].disconnect()
                except TypeError as e:
                    if "disconnect()" in str(e):
                        pass
                    else:
                        raise
        await self.app.remove_connection(connection)

    async def send_leave(self, connection, secret_key, password):
        return await self.app.documents_service.send_membership(connection, secret_key, password, "OUT")

    async def send_identity(self, connection, identity_doc):
        return await self.app.documents_service.broadcast_identity(connection, identity_doc)

    def generate_identity(self, connection):
        return self.app.documents_service.generate_identity(connection)

    def update_identity(self, identity):
        self.app.identities_service.insert_or_update_identity(identity)

    def notifications(self):
        return self.app.parameters.notifications

    @staticmethod
    def copy_pubkey_to_clipboard(connection):
        clipboard = QApplication.clipboard()
        clipboard.setText(connection.pubkey)

    @staticmethod
    def copy_pubkey_to_clipboard_with_crc(connection):
        clipboard = QApplication.clipboard()
        clipboard.setText(str(CRCPubkey.from_pubkey(connection.pubkey)))
