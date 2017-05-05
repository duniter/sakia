import asyncio
import pytest
from duniterpy.documents import Certification
from PyQt5.QtCore import QLocale, Qt, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from sakia.gui.sub.certification.controller import CertificationController
from ..helpers import click_on_top_message_box_button


@pytest.mark.asyncio
async def test_certification_init_community(application_with_one_connection, fake_server_with_blockchain, bob, alice):
    certification_dialog = CertificationController.create(None, application_with_one_connection)

    def close_dialog():
        if certification_dialog.view.isVisible():
            certification_dialog.view.hide()

    async def exec_test():
        certification_dialog.model.connection.password = bob.password
        QTest.keyClicks(certification_dialog.search_user.view.combobox_search.lineEdit(), "nothing")
        await asyncio.sleep(1)
        certification_dialog.search_user.view.search("")
        await asyncio.sleep(1)
        assert certification_dialog.user_information.model.identity is None
        assert not certification_dialog.view.button_process.isEnabled()
        certification_dialog.search_user.view.combobox_search.lineEdit().clear()
        QTest.keyClicks(certification_dialog.search_user.view.combobox_search.lineEdit(), alice.key.pubkey)
        await asyncio.sleep(0.1)
        certification_dialog.search_user.view.search("")
        await asyncio.sleep(1)
        certification_dialog.search_user.view.node_selected.emit(0)
        await asyncio.sleep(0.1)
        assert certification_dialog.user_information.model.identity.uid == "alice"
        await asyncio.sleep(0.1)
        assert certification_dialog.view.button_process.isEnabled()
        QTest.mouseClick(certification_dialog.view.button_process, Qt.LeftButton)
        await asyncio.sleep(0.1)
        QTest.mouseClick(certification_dialog.view.button_accept, Qt.LeftButton)
        await asyncio.sleep(0.1)
        QTest.keyClicks(certification_dialog.password_input.view.edit_secret_key, bob.salt)
        QTest.keyClicks(certification_dialog.password_input.view.edit_password, bob.password)
        assert certification_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        QTest.mouseClick(certification_dialog.view.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
        await asyncio.sleep(0.1)
        click_on_top_message_box_button(QMessageBox.Yes)
        await asyncio.sleep(0.2)
        assert isinstance(fake_server_with_blockchain.forge.pool[0], Certification)

    application_with_one_connection.loop.call_later(10, close_dialog)
    certification_dialog.view.show()
    await exec_test()
    close_dialog()
    await fake_server_with_blockchain.close()
