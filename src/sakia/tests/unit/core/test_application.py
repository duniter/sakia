import aiohttp
import sys
import unittest
import asyncio
from asynctest.mock import Mock, CoroutineMock, patch
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core import Application


class TestApplication(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.registry.IdentitiesRegistry')
    @patch('aiohttp.get', CoroutineMock(side_effect=lambda *args, **kwargs: exec('raise aiohttp.errors.TimeoutError()')))
    def test_get_last_version_timeout(self, identities_registry):
        app = Application(self.qapplication, self.lp, identities_registry)

        async def exec_test():
            app.get_last_version()
            asyncio.sleep(5)

        self.lp.run_until_complete(exec_test())
