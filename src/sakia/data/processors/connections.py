import attr
import sqlite3
import logging


@attr.s
class ConnectionsProcessor:
    """
    The processor of connections data.

    :param sakia.data.repositories.ConnectionsRepo _connections_repo: the repository of connections
    """

    _connections_repo = attr.ib()  # :type
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.connections_repo)

    def commit_connection(self, connection):
        """
        Saves a connection state in the db
        :param sakia.data.entities.Connection connection: the connection updated
        """
        try:
            self._connections_repo.insert(connection)
        except sqlite3.IntegrityError:
            self._connections_repo.update(connection)

    def remove_connections(self, connection):
        self._connections_repo.drop(connection)

    def pubkeys(self):
        return self._connections_repo.get_pubkeys()

    def connections(self):
        return self._connections_repo.get_all()

    def connections_with_uids(self, currency=""):
        if currency:
            return [r for r in self._connections_repo.get_all(currency=currency) if r.uid]
        else:
            return [r for r in self._connections_repo.get_all() if r.uid]

    def connections_to(self, currency):
        return self._connections_repo.get_all(currency=currency)

    def currencies(self):
        return self._connections_repo.get_currencies()
