import attr
from ..entities import Certification


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
