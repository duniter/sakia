import unittest
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.models.generic_tree import GenericTreeModel
from PyQt5.QtWidgets import QTreeView, QDialog


class TestGenericTree(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_generic_tree(self):
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