import attr

from duniterpy.documents import BlockUID, block_uid, MalformedDocumentError
from ..entities import Node


@attr.s(frozen=True)
class NodesRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (attr.fields(Node).currency, attr.fields(Node).pubkey)

    def insert(self, node):
        """
        Commit a node to the database
        :param sakia.data.entities.Node node: the node to commit
        """
        node_tuple = attr.astuple(node, tuple_factory=list)
        node_tuple[2] = "\n".join([str(n) for n in node_tuple[2]])
        node_tuple[12] = "\n".join([str(n) for n in node_tuple[12]])
        values = ",".join(['?'] * len(node_tuple))
        self._conn.execute("INSERT INTO nodes VALUES ({0})".format(values), node_tuple)

    def update(self, node):
        """
        Update an existing node in the database
        :param sakia.data.entities.Node node: the node to update
        """
        updated_fields = attr.astuple(node, tuple_factory=list,
                                      filter=attr.filters.exclude(*NodesRepo._primary_keys))
        updated_fields[0] = "\n".join([str(n) for n in updated_fields[0]])
        updated_fields[10] = "\n".join([str(n) for n in updated_fields[9]])
        where_fields = attr.astuple(node, tuple_factory=list,
                                    filter=attr.filters.include(*NodesRepo._primary_keys))
        self._conn.execute("""UPDATE nodes SET
                                    endpoints=?,
                                    peer_buid=?,
                                    uid=?,
                                    current_buid=?,
                                    current_ts=?,
                                    previous_buid=?,
                                    state=?,
                                    software=?,
                                    version=?,
                                    merkle_peers_root=?,
                                    merkle_peers_leaves=?,
                                    root=?,
                                    member=?,
                                    last_state_change=?
                                   WHERE
                                   currency=? AND
                                   pubkey=?""",
                                   updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing node in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Node
        """
        filters = []
        values = []
        for k, v in search.items():
            if isinstance(v, bool):
                v = int(v)
            filters.append("{k}=?".format(k=k))
            values.append(v)

        request = "SELECT * FROM nodes WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        data = c.fetchone()
        if data:
            return Node(*data)

    def get_all(self, **search):
        """
        Get all existing node in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Node
        """
        filters = []
        values = []
        for k, v in search.items():
            if isinstance(v, bool):
                value = int(v)
            else:
                value = v
            filters.append("{key} = ?".format(key=k))
            values.append(value)

        if filters:
            request = "SELECT * FROM nodes WHERE {filters}".format(filters=" AND ".join(filters))
        else:
            request = "SELECT * FROM nodes"

        c = self._conn.execute(request, tuple(values))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def drop(self, node):
        """
        Drop an existing node from the database
        :param sakia.data.entities.Node node: the node to update
        """
        where_fields = attr.astuple(node, filter=attr.filters.include(*NodesRepo._primary_keys))
        self._conn.execute("""DELETE FROM nodes
                              WHERE
                              currency=? AND pubkey=?""", where_fields)

    def get_offline_nodes(self, currency):
        c = self._conn.execute("SELECT * FROM nodes WHERE currency == ? AND state > ?;",
                               (currency, Node.FAILURE_THRESHOLD))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def get_synced_nodes(self, currency, current_buid):
        c = self._conn.execute("SELECT * FROM nodes "
                               "WHERE currency == ? "
                               "AND state <= ?"
                               "AND current_buid == ?",
                               (currency, Node.FAILURE_THRESHOLD, current_buid))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def get_synced_members_nodes(self, currency, current_buid):
        c = self._conn.execute("SELECT * FROM nodes "
                               "WHERE currency == ? "
                               "AND state <= ?"
                               "AND current_buid == ?"
                               "AND member == 1",
                               (currency, Node.FAILURE_THRESHOLD, current_buid))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def get_online_nodes(self, currency):
        c = self._conn.execute("SELECT * FROM nodes WHERE currency == ? AND state <= ?;",
                               (currency, Node.FAILURE_THRESHOLD))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def get_offline_synced_nodes(self, currency, current_buid):
        c = self._conn.execute("SELECT * FROM nodes "
                               "WHERE currency == ? "
                               "AND state > ?"
                               "AND current_buid == ?",
                               (currency, Node.FAILURE_THRESHOLD, current_buid))
        datas = c.fetchall()
        if datas:
            return [Node(*data) for data in datas]
        return []

    def current_buid(self, currency):
        c = self._conn.execute("""SELECT COUNT(`uid`)
        FROM `nodes`
        WHERE member == 1 AND currency == ?
        LIMIT 1;""", (currency,))
        data = c.fetchone()
        if data and data[0] > 3:
            c = self._conn.execute("""SELECT `current_buid`,
                 COUNT(`current_buid`) AS `value_occurrence`
        FROM     `nodes`
        WHERE member == 1 AND currency == ?
        GROUP BY `current_buid`
        ORDER BY `value_occurrence` DESC
        LIMIT    1;""", (currency,))
            data = c.fetchone()
            if data:
                return block_uid(data[0])
        else:
            c = self._conn.execute("""SELECT `current_buid`,
             COUNT(`current_buid`) AS `value_occurrence`
    FROM     `nodes`
    WHERE currency == ?
    GROUP BY `current_buid`
    ORDER BY `value_occurrence` DESC
    LIMIT    1;""", (currency,))
            data = c.fetchone()
            if data:
                return block_uid(data[0])

        return BlockUID.empty()
