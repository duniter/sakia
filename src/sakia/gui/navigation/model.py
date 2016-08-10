from ..component.model import ComponentModel
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
        :param sakia.core.app.Application app:
        """
        super().__init__(parent)
        self.app = app
        self.navigation = {}

    def init_navigation_data(self):
        self.navigation = [
            {
                'node': {
                    'title': self.app.current_account.name,
                    'component': "HomeScreen"
                },
                'children': []
            }
        ]
        for c in self.app.current_account.communities:
            self.navigation[0]['children'].append({
                'node': {
                    'title': c.currency,
                    'component': "Informations",
                    'community': c,
                    'account': self.app.current_account
                },
                'children': [
                    {
                        'node': {
                            'title': self.tr('Transfers'),
                            'icon': ':/icons/tx_icon',
                            'component': "TxHistory",
                            'community': c,
                            'account': self.app.current_account
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Network'),
                            'icon': ':/icons/network_icon',
                            'component': "Network",
                            'community': c,
                            'account': self.app.current_account
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Identities'),
                            'icon': ':/icons/members_icon',
                            'component': "Identities",
                            'community': c,
                            'account': self.app.current_account
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Web of Trust'),
                            'icon': ':/icons/wot_icon',
                            'component': "Wot",
                            'community': c,
                            'account': self.app.current_account
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Explorer'),
                            'icon': ':/icons/explorer_icon',
                            'component': "Explorer",
                            'community': c,
                            'account': self.app.current_account
                        }
                    }
                ]
            })
        return self.navigation

    def generic_tree(self):
        return GenericTreeModel.create("Navigation", self.navigation)
