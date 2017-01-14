from sakia.data.repositories import DividendsRepo
from sakia.data.entities import Dividend


def test_add_get_drop_dividend(meta_repo):
    dividends_repo = DividendsRepo(meta_repo.conn)
    dividends_repo.insert(Dividend("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               3, 1346543453, 1565, 1))
    dividend = dividends_repo.get_one(pubkey="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
    assert dividend.currency == "testcurrency"
    assert dividend.pubkey == "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
    assert dividend.timestamp == 1346543453
    assert dividend.block_number == 3
    assert dividend.base == 1
    assert dividend.amount == 1565

    dividends_repo.drop(dividend)
    source = dividends_repo.get_one(pubkey="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
    assert source is None


def test_add_get_multiple_dividends(meta_repo):
    dividends_repo = DividendsRepo(meta_repo.conn)
    dividends_repo.insert(Dividend("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               3, 1346543453, 1565, 1))
    dividends_repo.insert(Dividend("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               243, 4235252353, 45565, 2))
    dividends = dividends_repo.get_all(currency="testcurrency", pubkey="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
    assert "testcurrency" in [s.currency for s in dividends]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in [s.pubkey for s in dividends]
    assert 4235252353 in [s.timestamp for s in dividends]
    assert 1346543453 in [s.timestamp for s in dividends]
    assert 45565 in [s.amount for s in dividends]
    assert 1565 in [s.amount for s in dividends]
