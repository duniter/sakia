from typing import List

import attr

from ..entities import Blockchain, BlockchainParameters


@attr.s(frozen=True)
class BlockchainsRepo:
    """The repository for Blockchain entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (attr.fields(Blockchain).currency,)

    def insert(self, blockchain):
        """
        Commit a blockchain to the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to commit
        """
        blockchain_tuple = attr.astuple(blockchain.parameters) \
                           + attr.astuple(blockchain, filter=attr.filters.exclude(attr.fields(Blockchain).parameters))
        values = ",".join(['?'] * len(blockchain_tuple))
        self._conn.execute("INSERT INTO blockchains VALUES ({0})".format(values), blockchain_tuple)

    def update(self, blockchain):
        """
        Update an existing blockchain in the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to update
        """
        updated_fields = attr.astuple(blockchain, filter=attr.filters.exclude(
            attr.fields(Blockchain).parameters, *BlockchainsRepo._primary_keys))
        where_fields = attr.astuple(blockchain, filter=attr.filters.include(*BlockchainsRepo._primary_keys))
        self._conn.execute("""UPDATE blockchains SET
                          current_buid=?,
                          current_members_count=?,
                          current_mass=?,
                          median_time=?,
                          last_mass=?,
                          last_members_count=?,
                          last_ud=?,
                          last_ud_base=?,
                          last_ud_time=?,
                          previous_mass=?,
                          previous_members_count=?,
                          previous_ud=?,
                          previous_ud_base=?,
                          previous_ud_time=?
                           WHERE
                          currency=?""",
                           updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing blockchain in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Blockchain
        """
        filters = []
        values = []
        for k, v in search.items():
            filters.append("{k}=?".format(k=k))
            values.append(v)

        if filters:
            request = "SELECT * FROM blockchains WHERE {filters}".format(filters=" AND ".join(filters))
        else:
            request = "SELECT * FROM blockchains"

        c = self._conn.execute(request, tuple(values))
        data = c.fetchone()
        if data:
            return Blockchain(BlockchainParameters(*data[:20]), *data[20:])

    def get_all(self, offset=0, limit=1000, sort_by="currency", sort_order="ASC", **search) -> List[Blockchain]:
        """
        Get all existing blockchain in the database corresponding to the search
        :param int offset: offset in results to paginate
        :param int limit: limit results to paginate
        :param str sort_by: column name to sort by
        :param str sort_order: sort order ASC or DESC
        :param dict search: the criterions of the lookup
        :rtype: [sakia.data.entities.Blockchain]
        """
        filters = []
        values = []
        if search:
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = """SELECT * FROM blockchains WHERE {filters}
                          ORDER BY {sort_by} {sort_order}
                          LIMIT {limit} OFFSET {offset}""".format(
                filters=" AND ".join(filters),
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            c = self._conn.execute(request, tuple(values))
        else:
            request = """SELECT * FROM blockchains
                          ORDER BY {sort_by} {sort_order}
                          LIMIT {limit} OFFSET {offset}""".format(
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            c = self._conn.execute(request)
        datas = c.fetchall()
        if datas:
            return [Blockchain(BlockchainParameters(*data[:19]), *data[20:]) for data in datas]
        return []

    def drop(self, blockchain):
        """
        Drop an existing blockchain from the database
        :param sakia.data.entities.Blockchain blockchain: the blockchain to update
        """
        where_fields = attr.astuple(blockchain, filter=attr.filters.include(*BlockchainsRepo._primary_keys))
        self._conn.execute("DELETE FROM blockchains WHERE currency=?", where_fields)
