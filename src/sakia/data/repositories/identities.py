import attr

from duniterpy.documents.block import BlockUID

from ..entities import Identity


@attr.s(frozen=True)
class IdentitiesRepo:
    """The repository for Identities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (attr.fields(Identity).currency, attr.fields(Identity).pubkey, attr.fields(Identity).uid, attr.fields(Identity).blockstamp)

    def insert(self, identity):
        """
        Commit an identity to the database
        :param sakia.data.entities.Identity identity: the identity to commit
        """
        identity_tuple = attr.astuple(identity)
        values = ",".join(['?'] * len(identity_tuple))
        self._conn.execute("INSERT INTO identities VALUES ({0})".format(values), identity_tuple)

    def update(self, identity):
        """
        Update an existing identity in the database
        :param sakia.data.entities.Identity identity: the identity to update
        """
        updated_fields = attr.astuple(identity, filter=attr.filters.exclude(*IdentitiesRepo._primary_keys))
        where_fields = attr.astuple(identity, filter=attr.filters.include(*IdentitiesRepo._primary_keys))
        self._conn.execute("""UPDATE identities SET
                              signature=?,
                              timestamp=?,
                              written=?,
                              revoked_on=?,
                              outdistanced=?,
                              member=?,
                              ms_buid=?,
                              ms_timestamp=?,
                              ms_written_on=?,
                              ms_type=?,
                              sentry=?
                              WHERE
                              currency=? AND
                              pubkey=? AND
                              uid=? AND
                              blockstamp=?""", updated_fields + where_fields
                           )

    def get_one(self, **search):
        """
        Get an existing identity in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Identity
        """
        filters = []
        values = []
        for k, v in search.items():
            filters.append("{k}=?".format(k=k))
            values.append(v)

        request = "SELECT * FROM identities WHERE {filters}".format(filters=" AND ".join(filters))

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
        filters = []
        values = []
        for k, v in search.items():
            if isinstance(v, bool):
                v = int(v)
            filters.append("{k}=?".format(k=k))
            values.append(v)

        request = "SELECT * FROM identities WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        datas = c.fetchall()
        if datas:
            return [Identity(*data) for data in datas]
        return []

    def find_all(self, currency, text):
        """
        Get all existing identity in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Identity
        """
        request = "SELECT * FROM identities WHERE currency=? AND (UID LIKE ? or PUBKEY LIKE ?)"

        c = self._conn.execute(request, (currency, "%{0}%".format(text), "%{0}%".format(text)))
        datas = c.fetchall()
        if datas:
            return [Identity(*data) for data in datas]
        return []

    def drop(self, identity):
        """
        Drop an existing identity from the database
        :param sakia.data.entities.Identity identity: the identity to update
        """
        where_fields = attr.astuple(identity, filter=attr.filters.include(*IdentitiesRepo._primary_keys))
        self._conn.execute("""DELETE FROM identities WHERE
                           currency=? AND
                           pubkey=? AND
                           uid=? AND
                           blockstamp=?""", where_fields)
