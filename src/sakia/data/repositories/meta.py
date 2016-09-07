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
                               "CURRENCY varchar(30), "
                               "PUBKEY varchar(50),"
                               "UID varchar(255),"
                               "BLOCKSTAMP varchar(100),"
                               "SIGNATURE varchar(100),"
                               "TS int,"
                               "MEMBER boolean,"
                               "MS_BUID varchar(100),"
                               "MS_TIMESTAMP int,"
                               "PRIMARY KEY (CURRENCY, PUBKEY, UID, BLOCKSTAMP)"
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

