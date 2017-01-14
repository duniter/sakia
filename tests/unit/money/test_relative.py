import pytest
from sakia.money import Relative


def test_units(application_with_one_connection, bob):
    referential = Relative(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "UD TC"


def test_diff_units(application_with_one_connection, bob):
    referential = Relative(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "UD TC"


def test_value(application_with_one_connection, bob):
    referential = Relative(13555300, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == pytest.approx(58177.253218)


def test_differential(application_with_one_connection, bob):
    referential = Relative(11, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == pytest.approx(0.0472103)


def test_localized_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(11, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True)
    assert value == "0.047210 UD TC"


def test_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(1, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True, show_base=True)
    assert value == "0.004292 UD TC"


def test_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(11, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=False)
    assert value == "0.047210"


def test_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(1, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=True)
    assert value == "0.004292"


def test_diff_localized_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(11, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True)
    assert value == "0.047210 UD TC"


def test_diff_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(1, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True, show_base=True)
    assert value, "9.090909 x10⁻ UD TC"


def test_diff_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(1, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, show_base=False)
    assert value == "0.004292"


def test_diff_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Relative(1, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, show_base=True)
    assert value == "0.004292"
