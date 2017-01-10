import asyncio
import pytest
from duniterpy.documents import Certification
from PyQt5.QtCore import QLocale, Qt, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialogButtonBox, QApplication, QMessageBox
from sakia.gui.dialogs.certification.controller import CertificationController


@pytest.mark.asyncio
async def test_certification_init_community(application_with_one_connection, fake_server, bob, alice):
    certification_dialog = CertificationController.create(None, application_with_one_connection)

    def close_dialog():
        if certification_dialog.view.isVisible():
            certification_dialog.view.close()

    async def exec_test():
        certification_dialog.model.connection.password = bob.password
        QTest.keyClicks(certification_dialog.view.search_user.combobox_search.lineEdit(), "nothing")
        await asyncio.sleep(1)
        certification_dialog.search_user.view.search()
        await asyncio.sleep(1)
        assert certification_dialog.user_information.model.identity is None
        assert not certification_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        certification_dialog.view.search_user.combobox_search.lineEdit().clear()
        QTest.keyClicks(certification_dialog.view.search_user.combobox_search.lineEdit(), alice.key.pubkey)
        await asyncio.sleep(0.1)
        certification_dialog.search_user.view.search()
        await asyncio.sleep(0.1)
        certification_dialog.search_user.view.node_selected.emit(0)
        await asyncio.sleep(1)
        assert certification_dialog.user_information.model.identity.uid == "alice"
        assert certification_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        QTest.mouseClick(certification_dialog.view.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
        await asyncio.sleep(0.1)
        assert isinstance(fake_server.forge.pool[0], Certification)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await certification_dialog.async_exec()
    await fake_server.close()
