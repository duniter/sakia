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
    assert value == -10.79


def test_differential(application_with_one_connection, bob):
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.value()
    assert value == -10.79


def test_localized_no_si(application_with_one_connection, bob):
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True)
    assert value == "-10.79 Q0 TC"


def test_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=True, show_base=True)
    assert value == "1,088.11 Q0 TC"


def test_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=False)
    assert value == "-10.79"


def test_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.localized(units=False, show_base=True)
    assert value == "1,088.11 Q0"

    
def test_diff_localized_no_si(application_with_one_connection, bob):
    referential = QuantitativeZSum(110 * 1000, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=True)
    assert value == "1,100.00 TC"


def test_diff_localized_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101000000, bob.currency, application_with_one_connection, None)
    blockchain = application_with_one_connection.db.blockchains_repo.get_one(currency=bob.currency)
    blockchain.last_ud_base = 3
    application_with_one_connection.db.blockchains_repo.update(blockchain)
    value = referential.diff_localized(units=True, show_base=True)
    assert value == "1,010.00 x10³ TC"


def test_diff_localized_no_units_no_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101010110, bob.currency, application_with_one_connection, None)
    value = referential.diff_localized(units=False, show_base=False)
    assert value == "1,010,101.10"


def test_diff_localized_no_units_with_si(application_with_one_connection, bob):
    application_with_one_connection.parameters.digits_after_comma = 6
    referential = QuantitativeZSum(101000000, bob.currency, application_with_one_connection, None)
    blockchain = application_with_one_connection.db.blockchains_repo.get_one(currency=bob.currency)
    blockchain.last_ud_base = 3
    application_with_one_connection.db.blockchains_repo.update(blockchain)
    value = referential.diff_localized(units=False, show_base=True)
    assert value == "1,010.00 x10³"
