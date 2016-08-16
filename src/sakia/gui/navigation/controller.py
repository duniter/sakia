from .model import NavigationModel
from sakia.gui.component.controller import ComponentController
from .view import NavigationView
from .txhistory.controller import TxHistoryController
from .homescreen.controller import HomeScreenController
from .network.controller import NetworkController
from .identities.controller import IdentitiesController
from .informations.controller import InformationsController
from .graphs.wot.controller import WotController
from .graphs.explorer.controller import ExplorerController
from sakia.core import Account, Community
from PyQt5.QtCore import pyqtSignal


class NavigationController(ComponentController):
    """
    The navigation panel
    """
    community_changed = pyqtSignal(Community)
    account_changed = pyqtSignal(Account)

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.navigation.view view: the view
        :param sakia.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent, view, model)
        self.components = {
            'TxHistory': TxHistoryController,
            'HomeScreen': HomeScreenController,
            'Network': NetworkController,
            'Identities': IdentitiesController,
            'Informations': InformationsController,
            'Wot': WotController,
            'Explorer': ExplorerController
        }
        self.view.current_view_changed.connect(self.handle_view_change)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation component
        :param sakia.gui.agent.controller.AgentController parent:
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = NavigationView(parent.view)
        model = NavigationModel(None, app)
        navigation = cls(parent, view, model)
        model.setParent(navigation)
        navigation.init_navigation()
        return navigation

    @property
    def view(self) -> NavigationView:
        return self._view

    @property
    def model(self) -> NavigationModel:
        return self._model

    def init_navigation(self):
        def parse_node(node_data):
            if 'component' in node_data['node']:
                component_class = self.components[node_data['node']['component']]
                component = component_class.create(self, self.model.app, **node_data['node'])
                widget = self.view.add_widget(component.view)
                node_data['node']['widget'] = widget
            if 'children' in node_data:
                for child in node_data['children']:
                    parse_node(child)
            return node
        self.model.init_navigation_data()

        for node in self.model.navigation:
            parse_node(node)

        self.view.set_model(self.model)

    def handle_view_change(self, raw_data):
        """
        Handle view change
        :param dict raw_data:
        :return:
        """
        account = raw_data.get('account', None)
        community = raw_data.get('community', None)
        if account != self.model.current_data('account'):
            self.account_changed.emit(account)
        if community != self.model.current_data('community'):
            self.community_changed.emit(community)
        self.model.set_current_data(raw_data)
