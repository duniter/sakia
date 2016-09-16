import attr


@attr.s
class CommunityProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.CommunitiesRepo

    async def get_from_currency(self, currency):
        """
        Get the community of a currency

        :param currency:
        :rtype: sakia.data.entities.Community
        """
        return self._repo.get_one(currency=currency)

