import asyncio
import pytest
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QApplication
from sakia.gui.sub.transfer.controller import TransferController
from duniterpy.documents import Transaction


@pytest.mark.asyncio
async def test_transfer(application_with_one_connection, fake_server_with_blockchain, bob, alice):
    transfer_dialog = TransferController.create(None, application_with_one_connection)

    def close_dialog():
        if transfer_dialog.view.isVisible():
            transfer_dialog.view.hide()

    async def exec_test():
        QTest.mouseClick(transfer_dialog.view.radio_pubkey, Qt.LeftButton)
        QTest.keyClicks(transfer_dialog.view.edit_pubkey, alice.key.pubkey)
        transfer_dialog.view.spinbox_amount.setValue(10)
        await asyncio.sleep(0.1)
        assert not transfer_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        await asyncio.sleep(0.1)
        QTest.keyClicks(transfer_dialog.view.password_input.edit_secret_key, bob.salt)
        QTest.keyClicks(transfer_dialog.view.password_input.edit_password, bob.password)
        assert transfer_dialog.view.button_box.button(QDialogButtonBox.Ok).isEnabled()
        QTest.mouseClick(transfer_dialog.view.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
        await asyncio.sleep(0.2)
        assert isinstance(fake_server_with_blockchain.forge.pool[0], Transaction)

    application_with_one_connection.loop.call_later(10, close_dialog)
    transfer_dialog.view.show()
    await exec_test()
    #close_dialog()
    #await fake_server_with_blockchain.close()
