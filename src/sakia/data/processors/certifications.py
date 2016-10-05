import attr
from ..entities import Certification
import sqlite3


@attr.s
class CertificationsProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

    def create_certification(self, currency, cert, blockstamp):
        """
        Creates a certification and insert it in the db
        :param duniterpy.documents.Certification cert:
        :param duniterpy.documents.BlockUID blockstamp:
        :return: the instanciated certification
        :rtype: sakia.data.entities.Certification
        """
        cert = Certification(currency, cert.pubkey_from, cert.pubkey_to, cert.timestamp,
                             0, cert.signatures[0], blockstamp)
        self._repo.insert(cert)
        return cert

    def commit_certification(self, cert):
        """
        Commits a certification to the DB
        :param sakia.data.entities.Certification cert:
        :return:
        """
        try:
            self._repo.insert(cert)
        except sqlite3.IntegrityError:
            self._repo.update(cert)
