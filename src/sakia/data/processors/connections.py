import attr
import sqlite3
import logging


@attr.s
class ConnectionsProcessor:
    _connections_repo = attr.ib()  # :type sakia.data.repositories.ConnectionsRepo
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    def commit_connection(self, connection):
        """
        Saves a connection state in the db
        :param sakia.data.entities.Connection connection: the connection updated
        """
        try:
            self._connections_repo.insert(connection)
        except sqlite3.IntegrityError:
            self._connections_repo.update(connection)
