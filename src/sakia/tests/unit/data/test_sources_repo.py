from sakia.data.repositories import SourcesRepo
from sakia.data.entities import Source


def test_add_get_drop_source( meta_repo):
    sources_repo = SourcesRepo(meta_repo.conn)
    sources_repo.insert(Source("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               "0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843",
                               3,
                               "T",
                               1565,
                               1))
    source = sources_repo.get_one(identifier="0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843")
    assert source.currency == "testcurrency"
    assert source.pubkey == "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
    assert source.type == "T"
    assert source.amount == 1565
    assert source.base == 1
    assert source.noffset == 3

    sources_repo.drop(source)
    source = sources_repo.get_one(identifier="0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843")
    assert source is None


def test_add_get_multiple_source(meta_repo):
    sources_repo = SourcesRepo(meta_repo.conn)
    sources_repo.insert(Source("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               "0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843",
                               3,
                               "T",
                               1565,
                               1))
    sources_repo.insert(Source("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               "2pyPsXM8UCB88jP2NRM4rUHxb63qm89JMEWbpoRrhyDK",
                               22635,
                               "D",
                               726946,
                               1))
    sources = sources_repo.get_all(currency="testcurrency", pubkey="FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
    assert "testcurrency" in [s.currency for s in sources]
    assert "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn" in [s.pubkey for s in sources]
    assert "2pyPsXM8UCB88jP2NRM4rUHxb63qm89JMEWbpoRrhyDK" in [s.identifier for s in sources]
    assert "T" in [s.type for s in sources]
    assert "D" in [s.type for s in sources]
    assert 726946 in [s.amount for s in sources]
    assert 1565 in [s.amount for s in sources]
    assert "0835CEE9B4766B3866DD942971B3EE2CF953599EB9D35BFD5F1345879498B843" in [s.identifier for s in sources]
