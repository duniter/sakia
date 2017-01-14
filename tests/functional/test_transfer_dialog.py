import asyncio
import pytest
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QApplication
from sakia.gui.dialogs.transfer.controller import TransferController
from duniterpy.documents import Transaction


@pytest.mark.asyncio
async def test_transfer(application_with_one_connection, simple_fake_server, bob, alice):
    transfer_dialog = TransferController.create(None, application_with_one_connection)

    def close_dialog():
        if transfer_dialog.view.isVisible():
            transfer_dialog.view.close()

    async def exec_test():
        transfer_dialog.model.connection.password = bob.password
        QTest.mouseClick(transfer_dialog.view.radio_pubkey, Qt.LeftButton)
        QTest.keyClicks(transfer_dialog.view.edit_pubkey, alice.key.pubkey)
        transfer_dialog.view.spinbox_amount.setValue(10)
        await asyncio.sleep(0.1)
        assert transfer_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        QTest.mouseClick(transfer_dialog.view.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
        await asyncio.sleep(0.1)
        assert isinstance(simple_fake_server.forge.pool[0], Transaction)

    application_with_one_connection.loop.call_later(10, close_dialog)
    asyncio.ensure_future(exec_test())
    await transfer_dialog.async_exec()
    await simple_fake_server.close()
