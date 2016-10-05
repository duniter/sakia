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
from sakia.data.repositories import ConnectionsRepo
from PyQt5.QtCore import pyqtSignal


class NavigationController(ComponentController):
    """
    The navigation panel
    """
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
        view = NavigationView(None)
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
        user_identity = raw_data.get('user_identity', None)
        currency = raw_data.get('currency', None)
        if user_identity != self.model.current_data('user_identity'):
            self.account_changed.emit(user_identity)
        if currency != self.model.current_data('currency'):
            self.currency_changed.emit(currency)
        self.model.set_current_data(raw_data)
