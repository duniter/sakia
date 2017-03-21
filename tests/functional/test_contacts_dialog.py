import asyncio
import pytest
from sakia.data.entities import Contact
from PyQt5.QtCore import QLocale, Qt, QEvent, QModelIndex
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialogButtonBox
from sakia.gui.dialogs.contact.controller import ContactController
from ..helpers import click_on_top_message_box


@pytest.mark.asyncio
async def test_add_contact(application_with_one_connection, fake_server):
    contact_dialog = ContactController.create(None, application_with_one_connection)

    def close_dialog():
        if contact_dialog.view.isVisible():
            contact_dialog.view.close()

    async def exec_test():
        contact_dialog.view.edit_pubkey.setText("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        contact_dialog.view.edit_name.setText("john")
        QTest.mouseClick(contact_dialog.view.button_save, Qt.LeftButton)
        assert len(contact_dialog.view.table_contacts.model().sourceModel().contacts_data) == 1
        QTest.mouseClick(contact_dialog.view.button_box.button(QDialogButtonBox.Close), Qt.LeftButton)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await contact_dialog.async_exec()
    await fake_server.close()


@pytest.mark.asyncio
async def test_edit_contact(application_with_one_connection, fake_server):
    contacts_repo = application_with_one_connection.db.contacts_repo
    contacts_repo.insert(Contact(currency="test_currency",
                                 pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                 name="alice"))
    contact_dialog = ContactController.create(None, application_with_one_connection)

    def close_dialog():
        if contact_dialog.view.isVisible():
            contact_dialog.view.close()

    async def exec_test():
        contact_dialog.view.table_contacts.selectRow(0)
        contact_dialog.edit_contact()
        assert contact_dialog.view.edit_pubkey.text() == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        assert contact_dialog.view.edit_name.text() == "alice"
        contact_dialog.view.edit_name.setText("john")
        QTest.mouseClick(contact_dialog.view.button_save, Qt.LeftButton)
        assert len(contact_dialog.view.table_contacts.model().sourceModel().contacts_data) == 1
        assert contact_dialog.view.table_contacts.model().sourceModel().contacts_data[0][0] == "john"
        QTest.mouseClick(contact_dialog.view.button_box.button(QDialogButtonBox.Close), Qt.LeftButton)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await contact_dialog.async_exec()
    await fake_server.close()


@pytest.mark.asyncio
async def test_remove_contact(application_with_one_connection, fake_server):
    contacts_repo = application_with_one_connection.db.contacts_repo
    contacts_repo.insert(Contact(currency="test_currency",
                                 pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                 name="alice"))
    contact_dialog = ContactController.create(None, application_with_one_connection)

    def close_dialog():
        if contact_dialog.view.isVisible():
            contact_dialog.view.close()

    async def exec_test():
        contact_dialog.view.table_contacts.selectRow(0)
        contact_dialog.edit_contact()
        assert contact_dialog.view.edit_pubkey.text() == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        assert contact_dialog.view.edit_name.text() == "alice"
        contact_dialog.view.edit_name.setText("john")
        QTest.mouseClick(contact_dialog.view.button_delete, Qt.LeftButton)
        assert len(contact_dialog.view.table_contacts.model().sourceModel().contacts_data) == 0
        QTest.mouseClick(contact_dialog.view.button_box.button(QDialogButtonBox.Close), Qt.LeftButton)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await contact_dialog.async_exec()
    await fake_server.close()


@pytest.mark.asyncio
async def test_clear_selection(application_with_one_connection, fake_server):
    contacts_repo = application_with_one_connection.db.contacts_repo
    contacts_repo.insert(Contact(currency="test_currency",
                                 pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                 name="alice"))
    contact_dialog = ContactController.create(None, application_with_one_connection)

    def close_dialog():
        if contact_dialog.view.isVisible():
            contact_dialog.view.close()

    async def exec_test():
        contact_dialog.view.table_contacts.selectRow(0)
        contact_dialog.edit_contact()
        assert contact_dialog.view.edit_pubkey.text() == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        assert contact_dialog.view.edit_name.text() == "alice"
        contact_dialog.view.edit_name.setText("john")
        QTest.mouseClick(contact_dialog.view.button_clear, Qt.LeftButton)
        assert len(contact_dialog.view.table_contacts.model().sourceModel().contacts_data) == 1
        assert contact_dialog.view.edit_pubkey.text() == ""
        assert contact_dialog.view.edit_name.text() == ""
        contact_dialog.edit_contact()
        assert contact_dialog.view.edit_pubkey.text() == ""
        assert contact_dialog.view.edit_name.text() == ""

        QTest.mouseClick(contact_dialog.view.button_box.button(QDialogButtonBox.Close), Qt.LeftButton)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await contact_dialog.async_exec()
    await fake_server.close()
