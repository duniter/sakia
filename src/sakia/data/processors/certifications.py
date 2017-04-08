import attr
import asyncio
from duniterpy.api import bma, errors
from duniterpy.documents import block_uid
from ..connectors import BmaConnector
from ..processors import NodesProcessor
from ..entities import Certification, Identity
import sqlite3
import logging
from sakia.errors import NoPeerAvailable


@attr.s
class CertificationsProcessor:
    _certifications_repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _identities_repo = attr.ib()  # :type sakia.data.repositories.IdentitiesRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.certifications_repo, app.db.identities_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def drop_expired(self, identity, current_ts, sig_validity, sig_window):
        """
        Get the list of expired certifications to and from a given identity
        :param sakia.data.Identity identity:
        :rtype: List[sakia.data.entities.Certification]
        """
        expired = self._certifications_repo.expired(currency=identity.currency,
                                                    pubkey=identity.pubkey,
                                                    current_ts=current_ts,
                                                    sig_validity=sig_validity,
                                                    sig_window=sig_window)
        for cert in expired:
            self._certifications_repo.drop(cert)
        return expired

    def certifications_sent(self, currency, pubkey):
        """
        Get the list of certifications sent for a given pubkey
        :param str currency:
        :param str pubkey:
        :rtype: List[sakia.data.entities.Certification]
        """
        return self._certifications_repo.get_all(currency=currency, certifier=pubkey)

    def certifications_received(self, currency, pubkey):
        """
        Get the list of certifications sent for a given pubkey
        :param str currency:
        :param str pubkey:
        :rtype: List[sakia.data.entities.Certification]
        """
        return self._certifications_repo.get_all(currency=currency, certified=pubkey)

    def cert_issuance_delay(self, currency, pubkey, parameters, blockchain_time):
        """
        Get the remaining time before being able to issue new certification.
        :param str currency: the currency of the certifications
        :param str pubkey: the pubkey of the certifications
        :param sakia.data.entities.BlockchainParameters parameters: the parameters of the blockchain
        :param int blockchain_time: the current time of the blockchain
        :return: the remaining time
        :rtype: int
        """
        certified = self._certifications_repo.get_latest_sent(currency=currency, pubkey=pubkey)
        if certified and blockchain_time - certified.timestamp < parameters.sig_period:
            return parameters.sig_period - (blockchain_time - certified.timestamp)
        return 0

    def create_or_update_certification(self, currency, cert, timestamp, blockstamp):
        """
        Creates a certification and insert it in the db
        :param duniterpy.documents.Certification cert:
        :param int timestamp: the timestamp of the transaction
        :param duniterpy.documents.BlockUID blockstamp:
        :return: the instanciated certification
        :rtype: sakia.data.entities.Certification
        """
        cert = Certification(currency=currency,
                             certifier=cert.pubkey_from,
                             certified=cert.pubkey_to,
                             block=cert.timestamp.number,
                             timestamp=timestamp,
                             signature=cert.signatures[0],
                             written_on=blockstamp.number if blockstamp else -1)
        try:
            self._certifications_repo.insert(cert)
        except sqlite3.IntegrityError:
            self._certifications_repo.update(cert)
        return cert

    def insert_or_update_certification(self, cert):
        """
        Commits a certification to the DB
        :param sakia.data.entities.Certification cert:
        :return:
        """
        try:
            self._certifications_repo.insert(cert)
        except sqlite3.IntegrityError:
            self._certifications_repo.update(cert)

    def cleanup_connection(self, connection, connections_pubkeys):
        """
        Cleanup connections data after removal
        :param sakia.data.entities.Connection connection: removed connection
        :param List[str] connections_pubkeys: pubkeys of existing connections
        :return:
        """
        certifiers = self._certifications_repo.get_all(currency=connection.currency, certifier=connection.pubkey)
        for c in certifiers:
            if c.certified not in connections_pubkeys:
                self._certifications_repo.drop(c)

        certified = self._certifications_repo.get_all(currency=connection.currency, certified=connection.pubkey)
        for c in certified:
            if c.certifier not in connections_pubkeys:
                self._certifications_repo.drop(c)