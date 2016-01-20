import unittest
from asynctest.mock import Mock, CoroutineMock, patch, PropertyMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.money import QuantitativeZSum


class TestQuantitativeZSum(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = QuantitativeZSum(0, community, app, None)
        self.assertEqual(referential.units, "Q0 TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = QuantitativeZSum(0, community, app, None)
        self.assertEqual(referential.units, "Q0 TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_value(self, app, community):
        referential = QuantitativeZSum(110, community, app, None)
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 5})
        community.monetary_mass = CoroutineMock(return_value=500)
        async def exec_test():
            value = await referential.value()
            self.assertEqual(value, 10)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_differential(self, app, community):
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 5})
        community.monetary_mass = CoroutineMock(return_value=500)
        referential = QuantitativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.value()
            self.assertEqual(value, 10)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 5})
        community.monetary_mass = CoroutineMock(return_value=500)
        referential = QuantitativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True)
            self.assertEqual(value, "10 Q0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 1000})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(110 * 1000, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True, international_system=True)
            self.assertEqual(value, "109.500000 kQ0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 5})
        community.monetary_mass = CoroutineMock(return_value=500)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=False)
            self.assertEqual(value, "10")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 1000})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(110 * 1000, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=True)
            self.assertEqual(value, "109.500000 kQ0 ")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 1000})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000 * 1000)
        referential = QuantitativeZSum(110 * 1000, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True)
            self.assertEqual(value, "110,000 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 10})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000 * 1000)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(101010110, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True, international_system=True)
            self.assertEqual(value, "101.010110 MTC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 10})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000 * 1000)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(101010110, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=False)
            self.assertEqual(value, "101,010,110")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.get_ud_block = CoroutineMock(return_value={'membersCount': 10})
        community.monetary_mass = CoroutineMock(return_value=500 * 1000 * 1000)
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = QuantitativeZSum(101010110, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=True)
            self.assertEqual(value, "101.010110 M")
        self.lp.run_until_complete(exec_test())
