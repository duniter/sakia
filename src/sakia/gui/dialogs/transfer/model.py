import attr
from PyQt5.QtCore import QObject
from sakia.data.processors import BlockchainProcessor, SourcesProcessor, ConnectionsProcessor


@attr.s()
class TransferModel(QObject):
    """
    The model of transfer component

    :param sakia.app.Application app:
    :param sakia.data.entities.Connection connection:
    :param sakia.data.processors.BlockchainProcessor _blockchain_processor:
    """

    app = attr.ib()
    connection = attr.ib(default=None)
    resent_transfer = attr.ib(default=None)
    _blockchain_processor = attr.ib(default=None)
    _sources_processor = attr.ib(default=None)
    _connections_processor = attr.ib(default=None)

    def __attrs_post_init__(self):
        super().__init__()
        self._blockchain_processor = BlockchainProcessor.instanciate(self.app)
        self._sources_processor = SourcesProcessor.instanciate(self.app)
        self._connections_processor = ConnectionsProcessor.instanciate(self.app)

    def rel_to_quant(self, rel_value):
        """
        Get the quantitative value of a relative amount
        :param float rel_value:
        :rtype: int
        """
        dividend, base = self._blockchain_processor.last_ud(self.connection.currency)
        if base > 1:
            amount = rel_value * dividend
        else:
            amount = rel_value * dividend * 10**base
        # amount is rounded to the nearest power of 10 depending of last ud base
        # rounded = int(pow(10, base) * round(float(amount) / pow(10, base)))
        return int(amount) / 100

    def quant_to_rel(self, amount):
        """
        Get the relative value of a given amount
        :param int amount:
        :rtype: float
        """
        dividend, base = self._blockchain_processor.last_ud(self.connection.currency)
        if base > 1:
            relative = amount * 100 / dividend
        else:
            relative = amount * 100 / (dividend * 10**base)
        return relative

    def wallet_value(self):
        """
        Get the value of the current wallet in the current community
        """
        return self._sources_processor.amount(self.connection.currency, self.connection.pubkey)

    def current_base(self):
        """
        Get the current base of the network
        """
        dividend, base = self._blockchain_processor.last_ud(self.connection.currency)
        return base

    def localized_amount(self, amount):
        """
        Get the value of the current referential
        """
        localized = self.app.current_ref.instance(amount, self.connection.currency, self.app).diff_localized(False, True)
        return localized

    def cancel_previous(self):
        if self.resent_transfer:
            self.resent_transfer.cancel()

    def available_connections(self):
        return self._connections_processor.connections()

    def set_connection(self, index):
        connections = self._connections_processor.connections()
        self.connection = connections[index]

    async def send_money(self, recipient, secret_key, password, amount, amount_base, comment):
        """
        Send money to given recipient using the account
        :param str recipient:
        :param int amount:
        :param int amount_base:
        :param str comment:
        :param str password:
        :return: the result of the send
        """

        result, transactions = await self.app.documents_service.send_money(self.connection, secret_key, password,
                                                             recipient, amount, amount_base, comment)
        for transaction in transactions:
            self.app.sources_service.parse_transaction(self.connection.pubkey, transaction)
            if recipient in self._connections_processor.pubkeys():
                self.app.sources_service.parse_transaction(recipient, transaction)
            self.app.db.commit()
            self.app.sources_refreshed.emit()
        return result, transactions

    def notifications(self):
        return self.app.parameters.notifications

    def connection_pubkey(self, index):
        return self.available_connections()[index].pubkey
