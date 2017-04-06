import asyncio
import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from sakia.data.processors import ConnectionsProcessor
from sakia.gui.dialogs.connection_cfg import ConnectionConfigController
from tests.helpers import click_on_top_message_box, select_file_dialog


def assert_key_parameters_behaviour(connection_config_dialog, user):
    QTest.keyClicks(connection_config_dialog.view.edit_uid, user.uid)
    QTest.keyClicks(connection_config_dialog.view.edit_salt, user.salt)
    QTest.keyClicks(connection_config_dialog.view.edit_salt_bis, user.salt)
    assert connection_config_dialog.view.button_next.isEnabled() is False
    assert connection_config_dialog.view.button_generate.isEnabled() is False
    QTest.keyClicks(connection_config_dialog.view.edit_password, user.password)
    connection_config_dialog.view.button_next.isEnabled() is False
    connection_config_dialog.view.button_generate.isEnabled() is False
    QTest.keyClicks(connection_config_dialog.view.edit_password_repeat, user.password + "wrong")
    assert connection_config_dialog.view.button_next.isEnabled() is False
    assert connection_config_dialog.view.button_generate.isEnabled() is False
    connection_config_dialog.view.edit_password_repeat.setText("")
    QTest.keyClicks(connection_config_dialog.view.edit_password_repeat, user.password)
    assert connection_config_dialog.view.button_next.isEnabled() is True
    assert connection_config_dialog.view.button_generate.isEnabled() is True
    QTest.mouseClick(connection_config_dialog.view.button_generate, Qt.LeftButton)
    assert connection_config_dialog.view.label_info.text() == user.key.pubkey


def assert_pubkey_parameters_behaviour(connection_config_dialog, user):
    QTest.keyClicks(connection_config_dialog.view.edit_uid, user.uid)
    QTest.keyClicks(connection_config_dialog.view.edit_pubkey, user.key.pubkey)
    assert connection_config_dialog.view.button_next.isEnabled() is True


@pytest.mark.asyncio
async def test_register_empty_blockchain(application, fake_server, bob, tmpdir):
    tmpdir.mkdir("test_register")
    revocation_file = tmpdir.join("test_register").join("revocation.txt")
    identity_file = tmpdir.join("test_register").join("identity.txt")
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.mouseClick(connection_config_dialog.view.button_register, Qt.LeftButton)
        await asyncio.sleep(0.6)
        QTest.mouseClick(connection_config_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)

        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        assert_key_parameters_behaviour(connection_config_dialog, bob)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        connection_config_dialog.model.connection.password = bob.password
        await asyncio.sleep(1)
        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_services
        assert len(ConnectionsProcessor.instanciate(application).connections()) == 1
        click_on_top_message_box()
        await asyncio.sleep(1)
        select_file_dialog(str(identity_file))
        await asyncio.sleep(1)
        click_on_top_message_box()
        identity_file.ensure()
        await asyncio.sleep(1)
        select_file_dialog(str(revocation_file))
        await asyncio.sleep(1)
        click_on_top_message_box()
        await asyncio.sleep(1)
        revocation_file.ensure()

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()
    await fake_server.close()


@pytest.mark.asyncio
async def test_connect(application, fake_server_with_blockchain, bob):
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.mouseClick(connection_config_dialog.view.button_connect, Qt.LeftButton)
        await asyncio.sleep(0.6)
        QTest.mouseClick(connection_config_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)

        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        assert_key_parameters_behaviour(connection_config_dialog, bob)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        await asyncio.sleep(1)

        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_services
        assert len(ConnectionsProcessor.instanciate(application).connections()) == 1
        click_on_top_message_box()

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()
    await fake_server_with_blockchain.close()


@pytest.mark.asyncio
async def test_connect_wrong_uid(application, fake_server_with_blockchain, wrong_bob_uid, bob):
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.mouseClick(connection_config_dialog.view.button_connect, Qt.LeftButton)
        await asyncio.sleep(0.6)
        QTest.mouseClick(connection_config_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)
        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        assert_key_parameters_behaviour(connection_config_dialog, wrong_bob_uid)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        assert connection_config_dialog.view.label_info.text(), """Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(wrong_bob_uid.uid, bob.uid)
        connection_config_dialog.view.close()

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()
    await fake_server_with_blockchain.close()


@pytest.mark.asyncio
async def test_connect_wrong_pubkey(application, fake_server_with_blockchain, wrong_bob_pubkey, bob):
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.mouseClick(connection_config_dialog.view.button_connect, Qt.LeftButton)
        await asyncio.sleep(0.6)
        QTest.mouseClick(connection_config_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)
        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        assert_key_parameters_behaviour(connection_config_dialog, wrong_bob_pubkey)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        assert connection_config_dialog.view.label_info.text(), """Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(wrong_bob_pubkey.pubkey, bob.pubkey)
        connection_config_dialog.view.close()

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()
    await fake_server_with_blockchain.close()



@pytest.mark.asyncio
async def test_connect_pubkey_wrong_uid(application, fake_server_with_blockchain, wrong_bob_uid, bob):
    connection_config_dialog = ConnectionConfigController.create_connection(None, application)

    def close_dialog():
        if connection_config_dialog.view.isVisible():
            connection_config_dialog.view.close()

    async def exec_test():
        QTest.mouseClick(connection_config_dialog.view.button_pubkey, Qt.LeftButton)
        await asyncio.sleep(0.6)
        QTest.mouseClick(connection_config_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)
        assert connection_config_dialog.view.stacked_pages.currentWidget() == connection_config_dialog.view.page_connection
        assert_pubkey_parameters_behaviour(connection_config_dialog, wrong_bob_uid)
        QTest.mouseClick(connection_config_dialog.view.button_next, Qt.LeftButton)
        await asyncio.sleep(0.6)
        assert connection_config_dialog.view.label_info.text() == """Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(wrong_bob_uid.uid, bob.uid)
        connection_config_dialog.view.close()

    application.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await connection_config_dialog.async_exec()
    await fake_server_with_blockchain.close()
