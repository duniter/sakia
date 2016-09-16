import attr

from ..entities import Community


@attr.s(frozen=True)
class CommunitiesRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (Community.currency,)

    def insert(self, community):
        """
        Commit a community to the database
        :param sakia.data.entities.Community community: the community to commit
        """
        with self._conn:
            community_tuple = attr.astuple(community)
            values = ",".join(['?'] * len(community_tuple))
            self._conn.execute("INSERT INTO communities VALUES ({0})".format(values), community_tuple)

    def update(self, community):
        """
        Update an existing community in the database
        :param sakia.data.entities.Community community: the community to update
        """
        with self._conn:
            updated_fields = attr.astuple(community, filter=attr.filters.exclude(*CommunitiesRepo._primary_keys))
            where_fields = attr.astuple(community, filter=attr.filters.include(*CommunitiesRepo._primary_keys))
            self._conn.execute("""UPDATE communities SET
                              c=?,
                              dt=?,
                              ud0=?,
                              sig_period=?,
                              sig_stock=?,
                              sig_window=?,
                              sig_validity=?,
                              sig_qty=?,
                              xpercent=?,
                              ms_validity=?,
                              step_max=?,
                              median_time_blocks=?,
                              avg_gen_time=?,
                              dt_diff_eval=?,
                              blocks_rot=?,
                              percent_rot=?
                               WHERE
                              currency=?""",
                               updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing community in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Community
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM communities WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Community(*data)

    def get_all(self, **search):
        """
        Get all existing community in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Community
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                operator = "LIKE" if k == "currency" else "="
                value = "%{value}%".format(value=v) if k == "currency" else v
                filters.append("{key} {operator} ?".format(key=k, operator=operator))
                values.append(value)

            request = "SELECT * FROM communities WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Community(*data) for data in datas]
        return []

    def drop(self, community):
        """
        Drop an existing community from the database
        :param sakia.data.entities.Community community: the community to update
        """
        with self._conn:
            where_fields = attr.astuple(community, filter=attr.filters.include(*CommunitiesRepo._primary_keys))
            self._conn.execute("DELETE FROM communities WHERE currency=?", where_fields)
