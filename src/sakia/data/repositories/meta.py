import attr
import os
import logging
import sqlite3
from duniterpy.documents import BlockUID


@attr.s(frozen=True)
class MetaDatabase:
    """The repository for Identities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))
    db_file = 'sakia.db'

    @property
    def conn(self):
        return self._conn

    @classmethod
    def load_or_init(cls, config_path, profile_name):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        con = sqlite3.connect(os.path.join(config_path, profile_name, MetaDatabase.db_file),
                              detect_types=sqlite3.PARSE_DECLTYPES)
        meta = MetaDatabase(con)
        meta.prepare()
        meta.upgrade_database()
        return meta

    def prepare(self):
        """
        Prepares the database if the table is missing
        """
        with self._conn:
            self._logger.debug("Initializing meta database")
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
        self._logger.debug("Begin upgrade of database...")
        version = self.version()
        nb_versions = len(self.upgrades)
        for v in range(version, nb_versions):
            self._logger.debug("Upgrading to version {0}...".format(v))
            self.upgrades[v]()
            with self._conn:
                self._conn.execute("UPDATE meta SET version=? WHERE id=1", (version + 1,))
        self._logger.debug("End upgrade of database...")

    def create_all_tables(self):
        """
        Init all the tables
        :return:
        """
        self._logger.debug("Initialiazing all databases")
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
