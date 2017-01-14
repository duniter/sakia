from pytest import approx
from sakia.money import RelativeZSum


def test_units(application_with_one_connection, bob):
    referential = RelativeZSum(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "R0 TC"


def test_diff_units(application_with_one_connection, bob):
    referential = RelativeZSum(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "R0 TC"


def test_value(application_with_one_connection, bob):
    referential = RelativeZSum(2702, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == approx(8.70007)


def test_differential(application_with_one_connection, bob):
    referential = RelativeZSum(111, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == approx(-3.521619496)


def test_localized_no_si(application_with_one_connection, fake_server, bob):
    referential = RelativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True)
    assert value == "-3.53 R0 TC"


def test_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6

    referential = RelativeZSum(1, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True, show_base=True)
    assert value == "-4.040487 R0 TC"


def test_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6

    referential = RelativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=False)
    assert value == "-3.526336"


def test_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6

    referential = RelativeZSum(1, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=True)
    assert value == "-4.040487"


def test_diff_localized_no_si(application_with_one_connection, bob):
    referential = RelativeZSum(11, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True)
    assert value == "0.05 UD TC"


def test_diff_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6

    referential = RelativeZSum(1, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True, show_base=True)
    assert value == "0.004292 UD TC"


def test_diff_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = RelativeZSum(90, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, show_base=False)
    assert value == "0.386266"


def test_diff_localized_no_units_with_si(application_with_one_connection, bob):

    referential = RelativeZSum(90, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, show_base=True)
    assert value == "0.39"
