import attr

from ..entities import Transaction, Dividend


@attr.s(frozen=True)
class TransactionsRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (attr.fields(Transaction).currency, attr.fields(Transaction).pubkey, attr.fields(Transaction).sha_hash,)

    def insert(self, transaction):
        """
        Commit a transaction to the database
        :param sakia.data.entities.Transaction transaction: the transaction to commit
        """
        transaction_tuple = attr.astuple(transaction, tuple_factory=list)

        transaction_tuple[6] = "\n".join([str(n) for n in transaction_tuple[6]])
        transaction_tuple[7] = "\n".join([str(n) for n in transaction_tuple[7]])
        transaction_tuple[8] = "\n".join([str(n) for n in transaction_tuple[8]])

        values = ",".join(['?'] * len(transaction_tuple))
        self._conn.execute("INSERT INTO transactions VALUES ({0})".format(values), transaction_tuple)

    def update(self, transaction):
        """
        Update an existing transaction in the database
        :param sakia.data.entities.Transaction transaction: the transaction to update
        """
        updated_fields = attr.astuple(transaction, filter=attr.filters.exclude(*TransactionsRepo._primary_keys),
                                      tuple_factory=list)
        updated_fields[3] = "\n".join([str(n) for n in updated_fields[3]])
        updated_fields[4] = "\n".join([str(n) for n in updated_fields[4]])
        updated_fields[5] = "\n".join([str(n) for n in updated_fields[5]])

        where_fields = attr.astuple(transaction, filter=attr.filters.include(*TransactionsRepo._primary_keys),
                                    tuple_factory=list)
        self._conn.execute("""UPDATE transactions SET
                           written_on=?,
                           blockstamp=?,
                           ts=?,
                           signatures=?,
                           issuers = ?,
                           receivers = ?,
                           amount = ?,
                           amountbase = ?,
                           comment = ?,
                           txid = ?,
                           state = ?,
                           local = ?,
                           raw = ?
                           WHERE
                           currency=? AND
                           pubkey=? AND
                           sha_hash=?""",
                           updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing transaction in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Transaction
        """
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

    def get_transfers(self, currency, pubkey, offset=0, limit=1000, sort_by="currency", sort_order="ASC"):
        """
        Get all transfers in the database on a given currency from or to a pubkey

        :param str pubkey: the criterions of the lookup
        :rtype: List[sakia.data.entities.Transaction]
        """
        request = """SELECT * FROM transactions
                  WHERE currency=? AND pubkey=?
                  ORDER BY {sort_by} {sort_order}
                  LIMIT {limit} OFFSET {offset}""" \
                    .format(offset=offset,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order
                            )
        c = self._conn.execute(request, (currency, pubkey))
        datas = c.fetchall()
        if datas:
            return [Transaction(*data) for data in datas]
        return []

    def drop(self, transaction):
        """
        Drop an existing transaction from the database
        :param sakia.data.entities.Transaction transaction: the transaction to update
        """
        where_fields = attr.astuple(transaction, filter=attr.filters.include(*TransactionsRepo._primary_keys))
        self._conn.execute("""DELETE FROM transactions
                              WHERE
                              currency=? AND
                              pubkey=? AND
                              sha_hash=?""", where_fields)
