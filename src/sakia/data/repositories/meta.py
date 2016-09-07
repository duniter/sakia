import attr


@attr.s(frozen=True)
class MetaDatabase:
    """The repository for Identities entities.
    """

    _conn = attr.ib()  # :type sqlite3.Connection

    def prepare(self):
        """
        Prepares the database if the table is missing
        """
        with self._conn:
            self._conn.execute("create table if not exists meta("
                               "id integer not null,"
                               "version integer not null,"
                               "primary key (id)"
                               ")"
                               )

    @property
    def upgrades(self):
        return [
            self.create_all_tables,
        ]

    def upgrade_database(self):
        """
        Execute the migrations
        """
        version = self.version()
        nb_versions = len(self.upgrades)
        for v in range(version, nb_versions):
            self.upgrades[v]()
            with self._conn:
                self._conn.execute("UPDATE meta SET version=? WHERE id=1", (version + 1,))

    def create_all_tables(self):
        """
        Init all the tables
        :return:
        """
        with self._conn:
            self._conn.execute("create table if not exists identities("
                               "currency varchar(30), "
                               "pubkey varchar(50),"
                               "uid varchar(255),"
                               "blockstamp varchar(100),"
                               "signature varchar(100),"
                               "ts int,"
                               "revoked boolean,"
                               "member boolean,"
                               "ms_buid varchar(100),"
                               "ms_timestamp int,"
                               "PRIMARY KEY (currency, pubkey, uid, blockstamp)"
                               ")"
                               )

    def version(self):
        with self._conn:
            c = self._conn.execute("SELECT * FROM meta WHERE id=1")
            data = c.fetchone()
            if data:
                return data[1]
            else:
                self._conn.execute("INSERT INTO meta VALUES (1, 0)")
                return 0

