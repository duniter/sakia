from PyQt5.QtCore import QModelIndex
from sakia.models.generic_tree import GenericTreeModel


def test_generic_tree():
    data = [
        {
            'node': {
                'title': "Default Profile"
            },
            'children': [
                {
                    'node': {
                        'title': "Test net (inso)"
                    },
                    'children': [
                        {
                            'node': {
                                'title': "Transactions"
                            },
                            'children': []
                        },
                        {
                            'node': {
                                'title': "Network"
                            },
                            'children': []
                        }
                    ]
                },
                {
                    'node': {
                        'title': "Le sou"
                    },
                    'children': [
                        {
                            'node': {
                                'title': "Transactions"
                            },
                            'children': {}
                        },
                        {
                            'node': {
                                'title': "Network"
                            },
                            'children': {
                            }
                        }
                    ]
                }
            ],
        }
    ]
    tree_model = GenericTreeModel.create("Test", data)
    assert tree_model.columnCount(QModelIndex()) == 1
    assert tree_model.rowCount(QModelIndex()) == 1
