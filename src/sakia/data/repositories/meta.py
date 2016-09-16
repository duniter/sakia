import attr
import os


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
            self._conn.execute("""CREATE TABLE IF NOT EXISTS meta(
                               id INTEGER NOT NULL,
                               version INTEGER NOT NULL,
                               PRIMARY KEY (id)
                               )"""
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
        sql_file = open(os.path.join(os.path.dirname(__file__), 'meta.sql'), 'r')
        with self._conn:
            self._conn.executescript(sql_file.read())

    def version(self):
        with self._conn:
            c = self._conn.execute("SELECT * FROM meta WHERE id=1")
            data = c.fetchone()
            if data:
                return data[1]
            else:
                self._conn.execute("INSERT INTO meta VALUES (1, 0)")
                return 0
