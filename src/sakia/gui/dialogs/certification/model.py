from PyQt5.QtCore import QObject
from sakia.data.processors import IdentitiesProcessor, CertificationsProcessor, \
    BlockchainProcessor, ConnectionsProcessor
import attr


@attr.s()
class CertificationModel(QObject):
    """
    The model of Certification component
    """

    app = attr.ib()
    connection = attr.ib(default=None)
    _connections_processor = attr.ib(default=None)
    _certifications_processor = attr.ib(default=None)
    _identities_processor = attr.ib(default=None)
    _blockchain_processor = attr.ib(default=None)

    def __attrs_post_init__(self):
        super().__init__()
        self._connections_processor = ConnectionsProcessor.instanciate(self.app)
        self._certifications_processor = CertificationsProcessor.instanciate(self.app)
        self._identities_processor = IdentitiesProcessor.instanciate(self.app)
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)

    def change_connection(self, index):
        """
        Change current currency
        :param int index: index of the community in the account list
        """
        self.connection = self.connections_repo.get_currencies()[index]

    def get_cert_stock(self):
        """

        :return: the certifications stock
        :rtype: int
        """
        return self._blockchain_processor.parameters(self.connection.currency).sig_stock

    def remaining_time(self):
        """
        Get remaining time as a tuple to display
        :return: a tuple containing (days, hours, minutes, seconds)
        :rtype: tuple[int]
        """
        parameters = self._blockchain_processor.parameters(self.connection.currency)
        blockchain_time = self._blockchain_processor.time(self.connection.currency)
        remaining_time = self._certifications_processor.cert_issuance_delay(self.connection.currency,
                                                                            self.connection.pubkey,
                                                                            parameters, blockchain_time)

        days, remainder = divmod(remaining_time, 3600 * 24)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return days, hours, minutes, seconds

    def nb_certifications(self):
        """
        Get
        :return: a tuple containing (written valid certifications, pending certifications)
        :rtype: tuple[int]
        """
        certifications = self._certifications_processor.certifications_sent(self.connection.currency,
                                                                            self.connection.pubkey)
        nb_certifications = len([c for c in certifications if c.written_on])
        nb_cert_pending = len([c for c in certifications if not c.written_on])
        return nb_certifications, nb_cert_pending

    def could_certify(self):
        """
        Check if the user could theorically certify
        :return: true if the user can certifiy
        :rtype: bool
        """
        identity = self._identities_processor.get_identity(self.connection.currency,
                                                            self.connection.pubkey,
                                                            self.connection.uid)

        return identity.member

    def available_connections(self):
        return self._connections_processor.connections_with_uids()

    def set_connection(self,  index):
        connections = self._connections_processor.connections_with_uids()
        self.connection = connections[index]

    def notification(self):
        return self.app.parameters.notifications

    async def certify_identity(self, password, identity):
        result = await self.app.documents_service.certify(self.connection, password, identity)
        if result[0]:
            connection_identity = self._identities_processor.get_identity(self.connection.currency,
                                                                          self.connection.pubkey,
                                                                          self.connection.uid)
            self.app.identity_changed.emit(connection_identity)
            self.app.identity_changed.emit(identity)
        return result
