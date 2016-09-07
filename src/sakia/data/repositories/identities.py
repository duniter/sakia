import attr
from ..entities import Identity


@attr.s(frozen=True)
class IdentitiesRepo:
    """The repository for Identities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection

    def insert(self, identity):
        """
        Commit an identity to the database
        :param sakia.data.entities.Identity identity: the identity to commit
        """
        with self._conn:
            self._conn.execute("INSERT INTO identities VALUES (?,?,?,?,?,?,?,?,?,?)", attr.astuple(identity))

    def update(self, identity):
        """
        Update an existing identity in the database
        :param sakia.data.entities.Identity identity: the identity to update
        """
        with self._conn:
            self._conn.execute("UPDATE identities SET "
                              "signature=?, "
                              "ts=?,"
                              "revoked=?"
                              "member=?,"
                              "ms_buid=?,"
                              "ms_timestamp=?"
                              "WHERE "
                              "currency=? AND "
                              "pubkey=? AND "
                              "uid=? AND "
                              "blockstamp=?", attr.astuple(identity)[4:] + (identity.currency,
                                                                               identity.pubkey,
                                                                               identity.uid,
                                                                               identity.blockstamp)
                              )

    def get_one(self, **search):
        """
        Get an existing identity in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Identity
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM identities WHERE "
            request += " AND ".join(filters)

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Identity(*data)

    def get_all(self, **search):
        """
        Get all existing identity in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Identity
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM identities WHERE "
            request += " AND ".join(filters)

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Identity(*data) for data in datas]
        return []

    def drop(self, currency, pubkey):
        """
        Drop an existing identity from the database
        :param str currency:
        :param str pubkey:
        """
        with self._conn:
            self._conn.execute("DELETE FROM identities WHERE currency=? AND pubkey=?", (currency, pubkey))