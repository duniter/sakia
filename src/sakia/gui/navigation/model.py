from ..agent.model import AgentModel
from sakia.models.generic_tree import GenericTreeModel


class NavigationModel(AgentModel):
    """
    The model of Navigation agent
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def tree(self):
        navigation = [{'node': {
                            'title': self.app.current_account.name
                        },
                        'children': []
                        }
                    ]
        for c in self.app.current_account.communities:
            navigation[0]['children'].append({
                'node': {
                    'title': c.currency
                },
                'children': [
                    {
                        'node': {
                            'title': self.tr('Transfers')
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Network')
                        }
                    },
                    {
                        'node': {
                            'title': self.tr('Network')
                        }
                    }
                ]
            })
        return GenericTreeModel.create("Navigation", navigation)
