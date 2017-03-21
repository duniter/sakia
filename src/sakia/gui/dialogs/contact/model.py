from PyQt5.QtCore import QObject, Qt
from sakia.data.entities import Contact
from sakia.data.processors import IdentitiesProcessor, ContactsProcessor, \
    BlockchainProcessor, ConnectionsProcessor
from sakia.helpers import timestamp_to_dhms
from .table_model import ContactsTableModel, ContactsFilterProxyModel
import attr


@attr.s()
class ContactModel(QObject):
    """
    The model of Contact component
    """

    app = attr.ib()
    selected_id = attr.ib(default=-1)
    _contacts_processor = attr.ib(default=None)

    def __attrs_post_init__(self):
        super().__init__()
        self._contacts_processor = ContactsProcessor.instanciate(self.app)

    def init_contacts_table(self):
        """
        Generates a contacts table model
        :return:
        """
        self._model = ContactsTableModel(self, self.app)
        self._proxy = ContactsFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setDynamicSortFilter(True)
        self._proxy.setSortRole(Qt.DisplayRole)
        self._model.init_contacts()
        return self._proxy

    def save_contact(self, name, pubkey, contact_id):
        contact = Contact(self.app.currency, name, pubkey, contact_id=contact_id)
        self._contacts_processor.commit(contact)
        self._model.add_or_edit_contact(contact)

    def delete_contact(self, contact):
        self._contacts_processor.delete(contact)
        self._model.remove_contact(contact)

    def contact(self, index):
        contact_id = self._proxy.contact_id(index)
        if contact_id >= 0:
            return self._contacts_processor.contact(contact_id)
