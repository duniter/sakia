import unittest
from asynctest.mock import Mock, CoroutineMock, patch, PropertyMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.money import Relative


class TestRelative(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = Relative(0, community, app, None)
        self.assertEqual(referential.units, "UD TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = Relative(0, community, app, None)
        self.assertEqual(referential.units, "UD TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_value(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        referential = Relative(10101011, community, app, None)
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 1010.10110)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_differential(self, app, community):
        community.dividend = CoroutineMock(return_value=1000)
        referential = Relative(110, community, app, None)
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 0.11)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(101, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True)
            self.assertEqual(value, "0.101000 UD TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True, international_system=True)
            self.assertEqual(value, "1.011000 dUD TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=False)
            self.assertEqual(value, "0.101100")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=True)
            self.assertEqual(value, "1.011000 dUD ")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True)
            self.assertEqual(value, "0.101100 UD TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True, international_system=True)
            self.assertEqual(value, "1.011000 dUD TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=False)
            self.assertEqual(value, "0.101100")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = Relative(1011, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=True)
            self.assertEqual(value, "1.011000 dUD ")
        self.lp.run_until_complete(exec_test())