import unittest
from asynctest.mock import Mock, CoroutineMock, patch, PropertyMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.core.money import RelativeZSum


class TestRelativeZSum(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = RelativeZSum(0, community, app, None)
        self.assertEqual(referential.units, "R0 TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = RelativeZSum(0, community, app, None)
        self.assertEqual(referential.units, "R0 TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_value(self, app, community):
        referential = RelativeZSum(110, community, app, None)
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 0.10)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_differential(self, app, community):
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        referential = RelativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 0.10)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        referential = RelativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True)
            self.assertEqual(value, "0.1 R0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=True, international_system=True)
            self.assertEqual(value, "1.000000 dR0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=False)
            self.assertEqual(value, "0.100000")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(110, community, app, None)
        async def exec_test():
            value = await referential.localized(units=False, international_system=True)
            self.assertEqual(value, "1.000000 dR0 ")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        referential = RelativeZSum(90, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True)
            self.assertEqual(value, "0.9 R0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(90, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=True, international_system=True)
            self.assertEqual(value, "9.000000 dR0 TC")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_no_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(90, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=False)
            self.assertEqual(value, "0.900000")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_with_si(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        community.dividend = CoroutineMock(return_value=100)
        community.get_ud_block = CoroutineMock(side_effect=lambda *args, **kwargs: \
                                                            {'membersCount': 5, "monetaryMass": 500, "dividend": 100} if 'x' in kwargs \
                                                            else {'membersCount': 5, "monetaryMass": 1050, "dividend": 100} )
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeZSum(90, community, app, None)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=True)
            self.assertEqual(value, "9.000000 dR0 ")
        self.lp.run_until_complete(exec_test())
