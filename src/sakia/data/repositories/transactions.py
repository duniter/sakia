import attr

from ..entities import Transaction


@attr.s(frozen=True)
class TransactionsRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (Transaction.sha_hash,)

    def insert(self, transaction):
        """
        Commit a transaction to the database
        :param sakia.data.entities.Transaction transaction: the transaction to commit
        """
        with self._conn:
            transaction_tuple = attr.astuple(transaction)
            values = ",".join(['?'] * len(transaction_tuple))
            self._conn.execute("INSERT INTO transactions VALUES ({0})".format(values), transaction_tuple)

    def update(self, transaction):
        """
        Update an existing transaction in the database
        :param sakia.data.entities.Transaction transaction: the transaction to update
        """
        with self._conn:
            updated_fields = attr.astuple(transaction, filter=attr.filters.exclude(*TransactionsRepo._primary_keys))
            where_fields = attr.astuple(transaction, filter=attr.filters.include(*TransactionsRepo._primary_keys))
            self._conn.execute("""UPDATE transactions SET
                               currency=?,
                               written_on=?,
                               blockstamp=?,
                               ts=?,
                               signature=?,
                               issuer = ?,
                               receiver = ?,
                               amount = ?,
                               amountbase = ?,
                               comment = ?,
                               txid = ?
                               WHERE
                               sha_hash=?""",
                               updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing transaction in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Transaction
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM transactions WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Transaction(*data)

    def get_all(self, **search):
        """
        Get all existing transaction in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Transaction
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                value = v
                filters.append("{key} = ?".format(key=k))
                values.append(value)

            request = "SELECT * FROM transactions WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Transaction(*data) for data in datas]
        return []

    def drop(self, transaction):
        """
        Drop an existing transaction from the database
        :param sakia.data.entities.Transaction transaction: the transaction to update
        """
        with self._conn:
            where_fields = attr.astuple(transaction, filter=attr.filters.include(*TransactionsRepo._primary_keys))
            self._conn.execute("""DELETE FROM transactions
                                  WHERE
                                  sha_hash=?""", where_fields)
