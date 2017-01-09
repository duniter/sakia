from sakia.money import QuantitativeZSum


def test_units(application_with_one_connection, bob):
    referential = QuantitativeZSum(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "Q0 TC"


def test_diff_units(application_with_one_connection, bob):
    referential = QuantitativeZSum(0, bob.currency, application_with_one_connection, None)
    assert referential.units == "Q0 TC"


def test_value(application_with_one_connection, bob):
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == -1079


def test_differential(application_with_one_connection, bob):
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == -1079


def test_localized_no_si(application_with_one_connection, bob):
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True)
    assert value == "-1,079 Q0 TC"


def test_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True, international_system=True)
    assert value == "108.811000 x10³ Q0 TC"


def test_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, international_system=False)
    assert value == "-1,079"


def test_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, international_system=True)
    assert value == "108.811000 x10³ Q0"

    
def test_diff_localized_no_si(application_with_one_connection, bob):
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True)
    assert value == "110,000 TC"


def test_diff_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True, international_system=True)
    assert value == "101.010110 x10⁶ TC"


def test_diff_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, international_system=False)
    assert value == "101,010,110"


def test_diff_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, international_system=True)
    assert value == "101.010110 x10⁶"
