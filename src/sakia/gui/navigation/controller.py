from .model import NavigationModel
from .view import NavigationView
from .txhistory.controller import TxHistoryController
from .homescreen.controller import HomeScreenController
from .network.controller import NetworkController
from .identities.controller import IdentitiesController
from .informations.controller import InformationsController
from .graphs.wot.controller import WotController
from sakia.data.entities import Connection
from PyQt5.QtCore import pyqtSignal, QObject


class NavigationController(QObject):
    """
    The navigation panel
    """
    currency_changed = pyqtSignal(str)
    connection_changed = pyqtSignal(Connection)

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.navigation.view.NavigationView view: the view
        :param sakia.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.components = {
            'TxHistory': TxHistoryController,
            'HomeScreen': HomeScreenController,
            'Network': NetworkController,
            'Identities': IdentitiesController,
            'Informations': InformationsController,
            'Wot': WotController
        }
        self.view.current_view_changed.connect(self.handle_view_change)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation component
        :param sakia.app.Application app: the application
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = NavigationView(None)
        model = NavigationModel(None, app)
        navigation = cls(parent, view, model)
        model.setParent(navigation)
        navigation.init_navigation()
        app.new_connection.connect(navigation.add_connection)
        return navigation

    def parse_node(self, node_data):
        if 'component' in node_data:
            component_class = self.components[node_data['component']]
            component = component_class.create(self, self.model.app, **node_data['dependencies'])
            widget = self.view.add_widget(component.view)
            node_data['widget'] = widget
        if 'children' in node_data:
            for child in node_data['children']:
                self.parse_node(child)

    def init_navigation(self):
        self.model.init_navigation_data()

        for node in self.model.navigation:
            self.parse_node(node)

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

    def add_connection(self, connection):
        raw_node = self.model.add_connection(connection)
        self.view.add_connection(raw_node)
        self.parse_node(raw_node)
