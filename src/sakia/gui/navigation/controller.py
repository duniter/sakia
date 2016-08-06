from .model import NavigationModel
from ..component.controller import ComponentController
from .view import NavigationView
from ..txhistory.controller import TxHistoryController
from ..homescreen.controller import HomeScreenController
from ..network.controller import NetworkController


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
            'Identities': TxHistoryController
        }

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

