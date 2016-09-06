import attr
from ..entities import Identity


@attr.s
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
            self._conn.execute("INSERT INTO identities VALUES (?,?,?,?,?,?,?,?,?)", attr.astuple(identity))

    def update(self, identity):
        """
        Update an existing identity in the database
        :param sakia.data.entities.Identity identity: the identity to update
        """
        with self._conn:
            self.conn.execute("UPDATE identities SET "
                              "UID=?, "
                              "SIGNATURE=?, "
                              "BLOCKSTAMP=?,"
                              "TS=?,"
                              "MEMBER=?,"
                              "MS_BUID=?,"
                              "MS_TIMESTAMP=?"
                              "WHERE CURRENCY=? AND PUBKEY=?", attr.astuple(identity)[2:] + (identity.currency,
                                                                                         identity.pubkey)
                              )

    def get_one(self, currency, pubkey):
        """
        Get an existing identity in the database
        :param str currency:
        :param str pubkey:
        :rtype: sakia.data.entities.Identity
        """
        with self._conn:
            c = self._conn.execute("SELECT * FROM identities WHERE currency=? AND pubkey=?", (currency, pubkey))
            data = c.fetchone()
            if data:
                return Identity(*data)

    def drop(self, currency, pubkey):
        """
        Drop an existing identity from the database
        :param str currency:
        :param str pubkey:
        """
        with self._conn:
            self._conn.execute("DELETE FROM identities WHERE currency=? AND pubkey=?", (currency, pubkey))