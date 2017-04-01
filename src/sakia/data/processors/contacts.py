import attr
import sqlite3
import logging


@attr.s
class ContactsProcessor:
    """
    The processor of contacts data.

    :param sakia.data.repositories.ContactsRepo _contacts_repo: the repository of the contacts
    """
    _contacts_repo = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.contacts_repo)

    def contacts(self):
        return self._contacts_repo.get_all()

    def contact(self, contact_id):
        return self._contacts_repo.get_one(contact_id=contact_id)

    def commit(self, contact):
        try:
            self._contacts_repo.insert(contact)
        except sqlite3.IntegrityError:
            self._contacts_repo.update(contact)

    def delete(self, contact):
        self._contacts_repo.drop(contact)

    def get_one(self, **search):
        return self._contacts_repo.get_one(**search)
