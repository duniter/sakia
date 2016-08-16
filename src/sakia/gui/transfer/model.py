from sakia.gui.component.model import ComponentModel


class TransferModel(ComponentModel):
    """
    The model of transfer component
    """

    def __init__(self, parent, app, account, community, resent_transfer):
        super().__init__(parent)
        self.app = app
        self.account = account
        self.resent_transfer = resent_transfer
        self.community = community if community else self.account.communities[0]
        self.wallet = self.account.wallets[0]

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

    async def rel_to_quant(self, rel_value):
        """
        Get the quantitative value of a relative amount
        :param float rel_value:
        :rtype: int
        """
        ud_block = await self.community.get_ud_block()
        if ud_block:
            dividend = ud_block['dividend']
            base = ud_block['unitbase']
        else:
            dividend = 1
            base = 0
        amount = rel_value * dividend * pow(10, base)
        # amount is rounded to the nearest power of 10 depending of last ud base
        rounded = int(pow(10, base) * round(float(amount) / pow(10, base)))
        return rounded

    async def quant_to_rel(self, amount):
        """
        Get the relative value of a given amount
        :param int amount:
        :rtype: float
        """

        ud_block = await self.community.get_ud_block()
        if ud_block:
            dividend = ud_block['dividend']
            base = ud_block['unitbase']
        else:
            dividend = 1
            base = 0
        relative = amount / (dividend * pow(10, base))
        return relative

    async def wallet_value(self):
        """
        Get the value of the current wallet in the current community
        """
        return await self.wallet.value(self.community)

    async def current_base(self):
        """
        Get the current base of the network
        """
        ud_block = await self.community.get_ud_block()
        if ud_block:
            base = ud_block['unitbase']
        else:
            base = 0
        return base

    async def localized_amount(self, amount):
        """
        Get the value of the current referential
        """
        localized = await self.account.current_ref.instance(amount, self.community, self.app) \
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        return localized

    def change_community(self, index):
        """
        Change the current community
        :param int index: index in the list of communities
        """
        self.community = self.account.communities[index]

    def change_wallet(self, index):
        """
        Change the current wallet
        :param int index: index in the list of wallets
        """
        self.wallet = self.account.wallets[index]

    def cancel_previous(self):
        if self.resent_transfer:
            self.resent_transfer.cancel()

    async def send_money(self, recipient, amount, comment, password):
        """
        Send money to given recipient using the account
        :param str recipient:
        :param int amount:
        :param str comment:
        :param str password:
        :return: the result of the send
        """

        return await self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment)