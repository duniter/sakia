import attr
import asyncio
from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID
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
                   BmaConnector(NodesProcessor(app.db.nodes_repo)))

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

    def create_certification(self, currency, cert, blockstamp):
        """
        Creates a certification and insert it in the db
        :param duniterpy.documents.Certification cert:
        :param duniterpy.documents.BlockUID blockstamp:
        :return: the instanciated certification
        :rtype: sakia.data.entities.Certification
        """
        cert = Certification(currency, cert.pubkey_from, cert.pubkey_to, cert.timestamp.number,
                             0, cert.signatures[0], blockstamp)
        self._certifications_repo.insert(cert)
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

    async def initialize_certifications(self, identity, log_stream):
        """
        Initialize certifications to and from a given identity
        :param sakia.data.entities.Identity identity:
        :param function log_stream:
        """
        log_stream("Requesting certifiers of data")
        identities = list()
        certifiers = list()
        try:
            data = await self._bma_connector.get(identity.currency, bma.wot.certifiers_of,
                                                 req_args={'search': identity.pubkey})

            for certifier_data in data['certifications']:
                certification = Certification(currency=identity.currency,
                                              certified=identity.pubkey,
                                              certifier=certifier_data['pubkey'],
                                              block=certifier_data['cert_time']['block'],
                                              timestamp=certifier_data['cert_time']['medianTime'],
                                              signature=certifier_data['signature'])
                other_identity = Identity(currency=identity.currency,
                                          pubkey=certifier_data['pubkey'],
                                          uid=certifier_data['uid'],
                                          blockstamp=certifier_data['sigDate'],
                                          member=certifier_data['isMember'])
                if certifier_data['written']:
                    certification.written_on = BlockUID(certifier_data['written']['number'],
                                                        certifier_data['written']['hash'])

                certifiers.append(certification)
                identities.append(other_identity)
        except errors.DuniterError as e:
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                logging.debug("Certifiers of error : {0}".format(str(e)))
            else:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))

        log_stream("Requesting certified by data")
        certified = list()
        try:
            data = await self._bma_connector.get(identity.currency, bma.wot.certified_by, req_args={'search': identity.pubkey})
            for certified_data in data['certifications']:
                certification = Certification(currency=identity.currency,
                                              certifier=identity.pubkey,
                                              certified=certifier_data['pubkey'],
                                              block=certifier_data['cert_time']['block'],
                                              timestamp=certifier_data['cert_time']['medianTime'],
                                              signature=certifier_data['signature'])
                other_identity = Identity(currency=identity.currency,
                                          pubkey=certified_data['pubkey'],
                                          uid=certified_data['uid'],
                                          blockstamp=certified_data['sigDate'],
                                          member=certified_data['isMember'])
                if certified_data['written']:
                    certification.written_on = BlockUID(certified_data['written']['number'],
                                                        certified_data['written']['hash'])

                certified.append(certification)
                identities.append(other_identity)
        except errors.DuniterError as e:
            if e.ucode in (errors.NO_MATCHING_IDENTITY, errors.NO_MEMBER_MATCHING_PUB_OR_UID):
                logging.debug("Certified by error : {0}".format(str(e)))
        except NoPeerAvailable as e:
            logging.debug(str(e))

        log_stream('Commiting certifications...')
        for i, cert in enumerate(certifiers + certified):
            log_stream('Certification {0}/{1}'.format(i, len(certifiers + certified)))
            self.insert_or_update_certification(cert)
            await asyncio.sleep(0)

        log_stream('Commiting identities...')
        for i, idty in enumerate(identities):
            log_stream('Identity {0}/{1}'.format(i, len(identities)))
            try:
                self._identities_repo.insert(idty)
            except sqlite3.IntegrityError:
                self._identities_repo.update(idty)
            await asyncio.sleep(0)
