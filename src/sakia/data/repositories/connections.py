import attr

from ..entities import Connection


@attr.s(frozen=True)
class ConnectionsRepo:
    """
    The repository for Connections entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_connections = (Connection.currency, Connection.pubkey)

    def insert(self, connection):
        """
        Commit a connection to the database
        :param sakia.data.entities.Connection connection: the connection to commit
        """
        with self._conn:
            connection_tuple = attr.astuple(connection)
            values = ",".join(['?'] * len(connection_tuple))
            self._conn.execute("INSERT INTO connections VALUES ({0})".format(values), connection_tuple)

    def get_one(self, **search):
        """
        Get an existing connection in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Connection
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM connections WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Connection(*data)

    def get_all(self, **search):
        """
        Get all existing connection in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Connection
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                value = v
                filters.append("{connection} = ?".format(connection=k))
                values.append(value)

            request = "SELECT * FROM connections"
            if filters:
                request += "WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Connection(*data) for data in datas]
        return []

    def get_currencies(self):
        """
        Get all existing connection in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: List[str]
        """
        with self._conn:
            request = "SELECT UNIQUE currency FROM connections"
            c = self._conn.execute(request)
            datas = c.fetchall()
            if datas:
                return [Connection(*data) for data in datas]
        return []


    def drop(self, connection):
        """
        Drop an existing connection from the database
        :param sakia.data.entities.Connection connection: the connection to update
        """
        with self._conn:
            where_fields = attr.astuple(connection, filter=attr.filters.include(*ConnectionsRepo._primary_connections))
            self._conn.execute("""DELETE FROM connections
                                  WHERE
                                  currency=? AND
                                  pubkey=?""", where_fields)
