import asyncio
import logging
import sys
import pytest
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from sakia.data.processors import ConnectionsProcessor
from sakia.gui.dialogs.connection_cfg import ConnectionConfigController


@pytest.mark.asyncio
async def test_create_account(application, simple_fake_server, bob):
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.keyClicks(connection_config_dialog.view.lineedit_server, simple_fake_server.peer_doc().endpoints[0].ipv4)
        connection_config_dialog.view.spinbox_port.setValue(simple_fake_server.peer_doc().endpoints[0].port)
        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_node
        QTest.mouseClick(connection_config_dialog.view.button_register, Qt.LeftButton)
        await asyncio.sleep(1)

        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        QTest.keyClicks(connection_config_dialog.view.edit_salt, bob.salt)
        QTest.keyClicks(connection_config_dialog.view.edit_salt_bis, bob.salt)
        assert connection_config_dialog.view.button_next.isEnabled() is False
        assert connection_config_dialog.view.button_generate.isEnabled() is False
        QTest.keyClicks(connection_config_dialog.view.edit_password, bob.password)
        connection_config_dialog.view.button_next.isEnabled() is False
        connection_config_dialog.view.button_generate.isEnabled() is False
        QTest.keyClicks(connection_config_dialog.view.edit_password_repeat, bob.password + "wrong")
        assert connection_config_dialog.view.button_next.isEnabled() is False
        assert connection_config_dialog.view.button_generate.isEnabled() is False
        connection_config_dialog.view.edit_password_repeat.setText("")
        QTest.keyClicks(connection_config_dialog.view.edit_password_repeat, bob.password)
        assert connection_config_dialog.view.button_next.isEnabled() is True
        assert connection_config_dialog.view.button_generate.isEnabled() is True
        QTest.mouseClick(connection_config_dialog.view.button_generate, Qt.LeftButton)
        assert connection_config_dialog.view.label_info.text() == bob.key.pubkey
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        await asyncio.sleep(1)

        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page__communities
        await asyncio.sleep(1)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        assert len(ConnectionsProcessor.instanciate(application).connections(simple_fake_server.currency)) == 1

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()

