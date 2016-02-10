import unittest
from asynctest.mock import Mock, CoroutineMock, patch, PropertyMock
from PyQt5.QtCore import QLocale, QDateTime
from sakia.tests import QuamashTest
from sakia.core.money.relative_to_past import RelativeToPast


class TestRelativeToPast(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = RelativeToPast(0, community, app, 100)
        self.assertEqual(referential.units, "UD(t) TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_units(self, app, community):
        type(community).short_currency = PropertyMock(return_value="TC")
        referential = RelativeToPast(0, community, app, 100)
        self.assertEqual(referential.units, "UD(t) TC")

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_value(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        referential = RelativeToPast(10101011, community, app, 100)
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 1010.10110)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_differential(self, app, community):
        community.dividend = CoroutineMock(return_value=1000)
        referential = RelativeToPast(110, community, app, 100)
        async def exec_test():
            value = await referential.value()
            self.assertAlmostEqual(value, 0.11)
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(101, community, app, 100)
        async def exec_test():
            value = await referential.localized(units=True)
            self.assertEqual(value, "0.101000 UD({0}) TC".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.localized(units=True, international_system=True)
            self.assertEqual(value, "1.011000 mUD({0}) TC".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.localized(units=False, international_system=False)
            self.assertEqual(value, "0.101100")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_localized_no_units_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.localized(units=False, international_system=True)
            self.assertEqual(value, "1.011000 mUD({0}) ".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.diff_localized(units=True)
            self.assertEqual(value, "0.101100 UD({0}) TC".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.diff_localized(units=True, international_system=True)
            self.assertEqual(value, "1.011000 mUD({0}) TC".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_no_si(self, app, community):
        community.dividend = CoroutineMock(return_value=10000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=False)
            self.assertEqual(value, "0.101100")
        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Community')
    @patch('sakia.core.Application')
    def test_diff_localized_no_units_with_si(self, app, community):
        community.dividend = CoroutineMock(return_value=1000000)
        community.get_block = CoroutineMock(return_value={'medianTime': 1452663088792})
        type(community).short_currency = PropertyMock(return_value="TC")
        app.preferences = {
            'digits_after_comma': 6
        }
        referential = RelativeToPast(1011, community, app, 100)
        async def exec_test():
            value = await referential.diff_localized(units=False, international_system=True)
            self.assertEqual(value, "1.011000 mUD({0}) ".format(QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(1452663088792).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )))
        self.lp.run_until_complete(exec_test())
