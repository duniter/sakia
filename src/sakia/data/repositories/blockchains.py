import attr

from ..entities import Blockchain


@attr.s(frozen=True)
class BlockchainsRepo:
    """The repository for Blockchain entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (Blockchain.currency,)

    def insert(self, blockchain):
        """
        Commit a blockchain to the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to commit
        """
        with self._conn:
            blockchain_tuple = attr.astuple(blockchain)
            values = ",".join(['?'] * len(blockchain_tuple))
            self._conn.execute("INSERT INTO blockchains VALUES ({0})".format(values), blockchain_tuple)

    def update(self, blockchain):
        """
        Update an existing blockchain in the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to update
        """
        with self._conn:
            updated_fields = attr.astuple(blockchain, filter=attr.filters.exclude(*BlockchainsRepo._primary_keys))
            where_fields = attr.astuple(blockchain, filter=attr.filters.include(*BlockchainsRepo._primary_keys))
            self._conn.execute("""UPDATE blockchains SET
                              current_buid=?,
                              nb_members=?,
                              current_mass=?,
                              median_time=?,
                              last_ud=?,
                              last_ud_base=?,
                              previous_mass=?
                               WHERE
                              currency=?""",
                               updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing blockchain in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Blockchain
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM blockchains WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Blockchain(*data)

    def get_all(self, **search):
        """
        Get all existing blockchain in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Blockchain
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                operator = "LIKE" if k == "currency" else "="
                value = "%{value}%".format(value=v) if k == "currency" else v
                filters.append("{key} {operator} ?".format(key=k, operator=operator))
                values.append(value)

            request = "SELECT * FROM blockchains WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Blockchain(*data) for data in datas]
        return []

    def drop(self, blockchain):
        """
        Drop an existing blockchain from the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to update
        """
        with self._conn:
            where_fields = attr.astuple(blockchain, filter=attr.filters.include(*BlockchainsRepo._primary_keys))
            self._conn.execute("DELETE FROM blockchains WHERE currency=?", where_fields)
