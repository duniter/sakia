from sakia.gui.component.model import ComponentModel
from sakia.data.processors import IdentitiesProcessor, CertificationsProcessor, BlockchainProcessor


class CertificationModel(ComponentModel):
    """
    The model of Certification component
    """

    def __init__(self, parent, app, connection):
        """
        The data model of the certification dialog
        :param parent:
        :param sakia.app.Application app:
        :param sakia.data.entities.Connection connection: the connection used to certify
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self._certifications_processor = CertificationsProcessor.instanciate(app)
        self._identities_processor = IdentitiesProcessor.instanciate(app)
        self._blockchain_processor = BlockchainProcessor.instanciate(app)

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
        return self.blockchain_processor.parameters(self.currency).sig_stock

    def remaining_time(self):
        """
        Get remaining time as a tuple to display
        :return: a tuple containing (days, hours, minutes, seconds)
        :rtype: tuple[int]
        """
        remaining_time = self._certifications_processor.cert_issuance_delay(self.connection.currency,
                                                                            self.connection.pubkey)

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
        is_member = self._identities_processor.get_identity(self.connection.currency,
                                                            self.connection.pubkey,
                                                            self.connection.pubkey)

        return is_member and self._blockchain_processor.current_buid(self.connection.currency)
