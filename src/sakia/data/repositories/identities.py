import sqlite3
from ..entities import Identity


class IdentitiesRepo:
    def __init__(self, conn):
        """
        :param sqlite3.Connection conn: the cursor
        """
        self._conn = conn

    def prepare(self):
        """
        Prepares the database if the table is missing
        """
        with self._conn:
            self._conn.execute("create table if not exists identities("
                               "CURRENCY varchar(30), "
                               "PUBKEY varchar(50),"
                               "UID varchar(255),"
                               "SIGNATURE varchar(100),"
                               "BLOCKSTAMP varchar(100),"
                               "TS int,"
                               "MEMBER boolean,"
                               "MS_BUID varchar(100),"
                               "MS_TIMESTAMP int,"
                               "PRIMARY KEY (CURRENCY, PUBKEY)"
                               ")"
                               )

    def insert(self, identity):
        """
        Commit an identity to the database
        :param sakia.data.entities.Identity identity: the identity to commit
        """
        with self._conn:
            self._conn.execute("INSERT INTO identities VALUES (?,?,?,?,?,?,?,?,?)", identity.astuple())

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
                              "WHERE CURRENCY=? AND PUBKEY=?", identity.astuple()[2:] + (identity.currency,
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