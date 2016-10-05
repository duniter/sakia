from sakia.gui.component.model import ComponentModel
from duniterpy.api import errors
from sakia.errors import NoPeerAvailable

import logging


class CertificationModel(ComponentModel):
    """
    The model of Certification component
    """

    def __init__(self, parent, app, identity, currency,
                 connections_repo, identities_processor, blockchain_processor):
        """
        The data model of the certification dialog
        :param parent:
        :param sakia.app.Application app:
        :param sakia.data.entities.Identity identity: the identity of the certifier
        :param str currency:
        :param sakia.data.repositories.ConnectionsRepository connections_repo:
        :param sakia.data.processors.IdentitiesProcessor identities_processor:
        :param sakia.data.processors.BlockchainProcessor blockchain_processor:
        """
        super().__init__(parent)
        self.app = app
        self.currency = currency
        self.connections_repo = connections_repo
        self.identities_processor = identities_processor
        self.blockchain_processor = blockchain_processor

    def contact_name_pubkey(self, name):
        """
        Get the pubkey of a contact from its name
        :param str name:
        :return:
        :rtype: str
        """
        for contact in self.account.contacts:
            if contact['name'] == name:
                return contact['pubkey']

    def change_currency(self, index):
        """
        Change current currency
        :param int index: index of the community in the account list
        """
        self.currency = self.connections_repo.get_currencies()[index]

    def get_cert_stock(self):
        """

        :return: the certifications stock
        :rtype: int
        """
        return self.blockchain_processor.parameters(self.currency).sig_stock

    async def remaining_time(self):
        """
        Get remaining time as a tuple to display
        :return: a tuple containing (days, hours, minutes, seconds)
        :rtype: tuple[int]
        """
        remaining_time = await account_identity.cert_issuance_delay(self.app.identities_registry, self.currency)

        days, remainder = divmod(remaining_time, 3600 * 24)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return days, hours, minutes, seconds

    async def nb_certifications(self):
        """
        Get
        :return: a tuple containing (written valid certifications, pending certifications)
        :rtype: tuple[int]
        """
        account_identity = await self.account.identity(self.currency)
        certifications = await account_identity.unique_valid_certified_by(self.app.identities_registry, self.currency)
        nb_certifications = len([c for c in certifications if c['block_number']])
        nb_cert_pending = len([c for c in certifications if not c['block_number']])
        return nb_certifications, nb_cert_pending

    async def could_certify(self):
        """
        Check if the user could theorically certify
        :return: true if the user can certifiy
        :rtype: bool
        """
        account_identity = await self.account.identity(self.community)
        is_member = await account_identity.is_member(self.community)
        try:
            block_0 = await self.community.get_block(0)
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                block_0 = None
        except NoPeerAvailable as e:
            logging.debug(str(e))
            block_0 = None
        return is_member or not block_0