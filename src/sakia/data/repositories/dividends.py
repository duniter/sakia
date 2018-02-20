import attr

from ..entities import Dividend


@attr.s(frozen=True)
class DividendsRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (attr.fields(Dividend).currency, attr.fields(Dividend).pubkey, attr.fields(Dividend).block_number)

    def insert(self, dividend):
        """
        Commit a dividend to the database
        :param sakia.data.entities.Dividend dividend: the dividend to commit
        """
        dividend_tuple = attr.astuple(dividend)
        values = ",".join(['?'] * len(dividend_tuple))
        self._conn.execute("INSERT INTO dividends VALUES ({0})".format(values), dividend_tuple)

    def get_one(self, **search):
        """
        Get an existing dividend in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Dividend
        """
        filters = []
        values = []
        for k, v in search.items():
            filters.append("{k}=?".format(k=k))
            values.append(v)

        request = "SELECT * FROM dividends WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        data = c.fetchone()
        if data:
            return Dividend(*data)

    def get_all(self, **search):
        """
        Get all existing dividend in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Dividend
        """
        filters = []
        values = []
        for k, v in search.items():
            value = v
            filters.append("{key} = ?".format(key=k))
            values.append(value)

        request = "SELECT * FROM dividends WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        datas = c.fetchall()
        if datas:
            return [Dividend(*data) for data in datas]
        return []

    def get_dividends(self, currency, pubkey, offset=0, limit=1000, sort_by="currency", sort_order="ASC"):
        """
        Get all transfers in the database on a given currency from or to a pubkey

        :param str pubkey: the criterions of the lookup
        :rtype: List[sakia.data.entities.Dividend]
        """
        request = """SELECT * FROM dividends
                  WHERE currency=? AND pubkey=?
                  ORDER BY {sort_by} {sort_order}
                  LIMIT {limit} OFFSET {offset}""" \
                    .format(offset=offset,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order
                            )
        c = self._conn.execute(request, (currency, pubkey, pubkey))
        datas = c.fetchall()
        if datas:
            return [Dividend(*data) for data in datas]
        return []

    def drop(self, dividend):
        """
        Drop an existing dividend from the database
        :param sakia.data.entities.Dividend dividend: the dividend to update
        """
        where_fields = attr.astuple(dividend, filter=attr.filters.include(*DividendsRepo._primary_keys))
        self._conn.execute("""DELETE FROM dividends
                              WHERE
                              currency=? AND pubkey=? AND block_number=? """, where_fields)
