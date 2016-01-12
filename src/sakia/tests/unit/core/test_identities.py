import sys
import unittest
from unittest import mock
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import Identity, IdentitiesRegistry, LocalState, BlockchainState
from sakia.tests import QuamashTest


class TestIdentity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_identity_from_handled_data(self):
        community = mock.MagicMock()
        type(community).currency = mock.PropertyMock(return_value="test_currency")

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", None,
                            LocalState.COMPLETED, BlockchainState.VALIDATED)
        test_instances = {
            "test_currency": {"7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ": identity}
        }
        identities_registry = IdentitiesRegistry(test_instances)

        identity_from_data = identities_registry.from_handled_data("john",
                                                                    "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                                   None,
                                                                   BlockchainState.VALIDATED,
                                                                   community)
        self.assertEqual(identity, identity_from_data)

