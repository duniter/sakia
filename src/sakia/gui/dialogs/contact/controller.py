import asyncio

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication

from sakia.constants import ROOT_SERVERS
from sakia.decorators import asyncify
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from sakia.gui.sub.password_input import PasswordInputController
from sakia.gui.widgets import dialogs
from .model import ContactModel
from .view import ContactView
import attr


@attr.s()
class ContactController(QObject):
    """
    The Contact view
    """

    view = attr.ib()
    model = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.view.button_box.rejected.connect(self.view.close)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a Contact component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app: sakia application
        :return: a new Contact controller
        :rtype: ContactController
        """
        view = ContactView(parent.view if parent else None)
        model = ContactModel(app)
        contact = cls(view, model)
        view.set_table_contacts_model(model.init_contacts_table())
        view.button_save.clicked.connect(contact.save_contact)
        view.table_contacts.clicked.connect(contact.edit_contact)
        view.button_clear.clicked.connect(contact.clear_selection)
        view.button_delete.clicked.connect(contact.delete_contact)
        return contact

    @classmethod
    def open_dialog(cls, parent, app):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.core.Community community: the community
        :return:
        """
        dialog = cls.create(parent, app)
        return dialog.exec()

    def save_contact(self):
        name = self.view.edit_name.text()
        pubkey = self.view.edit_pubkey.text()
        contact_id = self.model.selected_id
        self.model.save_contact(name, pubkey, contact_id)
        self.view.edit_name.clear()
        self.view.edit_pubkey.clear()
        self.model.selected_id = -1

    def edit_contact(self):
        contact_index = self.view.selected_contact_index()
        contact = self.model.contact(contact_index)
        if contact:
            self.view.edit_pubkey.setText(contact.pubkey)
            self.view.edit_name.setText(contact.name)
            self.model.selected_id = contact.contact_id

    def delete_contact(self):
        contact_index = self.view.selected_contact_index()
        contact = self.model.contact(contact_index)
        if contact:
            self.model.delete_contact(contact)
            self.view.edit_pubkey.clear()
            self.view.edit_name.clear()
            self.model.selected_id = -1

    def clear_selection(self):
        self.view.edit_pubkey.clear()
        self.view.edit_name.clear()
        self.view.table_contacts.clearSelection()
        self.model.selected_id = -1

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        return future

    def exec(self):
        self.view.exec()
