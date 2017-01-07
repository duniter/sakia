from sakia.money import Quantitative


def test_units(application_with_one_connection, bob):
    referential = Quantitative(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "TC"


def test_diff_units(application_with_one_connection, bob):
    referential = Quantitative(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "TC"


def test_value(application_with_one_connection, bob):
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == 101010110


def test_differential(application_with_one_connection, bob):
    referential = Quantitative(110, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == 110


def test_localized_no_si(application_with_one_connection, bob):
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True)
    assert value == "101,010,110 TC"


def test_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True, international_system=True)
    assert value == "101.010110 x10⁶ TC"


def test_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, international_system=False)
    assert value == "101,010,110"


def test_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, international_system=True)
    assert value == "101.010110 x10⁶"


def test_diff_localized_no_si(application_with_one_connection, bob):
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True)
    assert value == "101,010,110 TC"


def test_diff_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True, international_system=True)
    assert value == "101.010110 x10⁶ TC"


def test_diff_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, international_system=False)
    assert value == "101,010,110"


def test_diff_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = Quantitative(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, international_system=True)
    assert value == "101.010110 M"
