from sakia.gui.component.model import ComponentModel
from sakia.models.generic_tree import GenericTreeModel
from PyQt5.QtCore import pyqtSignal


class NavigationModel(ComponentModel):
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
        self.navigation = {}
        self._current_data = None

    def init_navigation_data(self):
        self.navigation = [
            {
                'node': {
                    'title': self.app.parameters.profile_name,
                    'component': "HomeScreen",
                    'parameters': self.app.parameters
                },
                'children': []
            }
        ]
        self._current_data = self.navigation[0]
        for connection in self.app.db.connections_repo.get_all():
            self.navigation[0]['children'].append({
                'node': {
                    'title': connection.currency,
                    'component': "Informations",
                    'blockchain_service': self.app.blockchain_services[connection.currency],
                    'identities_service': self.app.identities_services[connection.currency],
                    'sources_service': self.app.sources_services[connection.currency],
                    'connection': connection,
                },
                'children': [
                   # {
                   #     'node': {
                   #         'title': self.tr('Transfers'),
                   #         'icon': ':/icons/tx_icon',
                   #         'component': "TxHistory",
                   #         'transactions_service': self.app.transactions_services[connection.currency],
                   #     }
                   # },
                    {
                        'node': {
                            'title': self.tr('Network'),
                            'icon': ':/icons/network_icon',
                            'component': "Network",
                            'network_service': self.app.network_services[connection.currency],
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Identities'),
                            'icon': ':/icons/members_icon',
                            'component': "Identities",
                            'connection': connection,
                            'blockchain_service': self.app.blockchain_services[connection.currency],
                            'identities_service': self.app.identities_services[connection.currency],
                        }
                    },
            #        {
            #            'node': {
            #                'title': self.tr('Web of Trust'),
            #                'icon': ':/icons/wot_icon',
            #                'component': "Wot",
            #            }
            #        }
                ]
            })
        return self.navigation

    def generic_tree(self):
        return GenericTreeModel.create("Navigation", self.navigation)

    def set_current_data(self, raw_data):
        self._current_data = raw_data

    def current_data(self, key):
        return self._current_data.get(key, None)
