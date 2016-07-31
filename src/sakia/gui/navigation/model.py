from PyQt5.QtCore import QAbstractItemModel, Qt, QVariant


class NavigationModel(QAbstractItemModel):
    """
    The model of Navigation agent
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def tree(self):
        navigation = {'profile': {
                        'node': {
                            'title': self.account.name
                        },
                        'children': {}
                        }
                    }
        for c in self.account.communities:
            navigation['profile']['children'].append({
                'node': {
                    'title': c.currency
                },
                'children': {
                    'transfers': {
                        'node': {
                            'title': self.tr('Transfers')
                        }
                    },
                    'network': {
                        'node': {
                            'title': self.tr('Network')
                        }
                    },
                    'network': {
                        'node': {
                            'title': self.tr('Network')
                        }
                    }
                }
            })

    def rowCount(self, parent):
        return len(self.nodes_data)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        return self.columns_types[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        node = self.nodes_data[row]
        if role == Qt.DisplayRole:
            return node[col]
        if role == Qt.BackgroundColorRole:
            return self.node_colors[node[self.columns_types.index('state')]]
        if role == Qt.ToolTipRole:
            return self.node_states[node[self.columns_types.index('state')]]()

        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

