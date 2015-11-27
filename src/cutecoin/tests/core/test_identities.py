import sys
import unittest
from unittest import mock
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from cutecoin.core.registry.identities import Identity, IdentitiesRegistry, LocalState, BlockchainState
from cutecoin.tests import get_application


class TestIdentity(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_identity_from_handled_data(self):
        community = mock.MagicMock()
        type(community).currency = mock.PropertyMock(return_value="test_currency")

        identity = Identity("john", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                            LocalState.COMPLETED, BlockchainState.VALIDATED)
        test_instances = {
            "test_currency": {"7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ": identity}
        }
        identities_registry = IdentitiesRegistry(test_instances)

        identity_from_data = identities_registry.from_handled_data("john",
                                                                    "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", BlockchainState.VALIDATED,
                                                                   community)
        self.assertEqual(identity, identity_from_data)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
